from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from .serializers import ReviewSerializer
import requests
from bs4 import BeautifulSoup
import re
from django.db import connection
from transformers import BartTokenizer, BartForConditionalGeneration
from googletrans import Translator, LANGUAGES
from langdetect import detect, LangDetectException

class ReviewList(APIView):
    def get(self, request, format=None):
        # Eliminar todos los registros existentes en la tabla antes de nuevas inserciones

        # Borrar todos los registros
        Review.objects.all().delete()

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='reviews_review'")

        # Hacer el web scraping
        urls = {
            'chevrolet-sail': 'https://www.opinautos.com/co/chevrolet/sail/opiniones',
            'toyota-hilux': 'https://www.opinautos.com/co/toyota/hilux/opiniones',
            'volkswagen-gol': 'https://www.opinautos.com/co/volkswagen/gol/opiniones'
        }

        for modelo, website in urls.items():
            resultado = requests.get(website)
            soup = BeautifulSoup(resultado.text, 'html.parser')
            reviews = soup.find_all("div", class_="WhiteCard margin-top desktop-margin15 js-review")

            for review in reviews:
                left_right_box = review.find("div", class_="LeftRightBox__left LeftRightBox__left--noshrink")
                star_count = 0
                if left_right_box:
                    align_middles = left_right_box.find_all("span", class_="align-middle inline-block")
                    for align_middle in align_middles:
                        icons = align_middle.find_all("img", class_="Icon")
                        star_count += sum(1 for icon in icons if icon.get("src") == "https://static.opinautos.com/images/design2/icons/icon_star--gold.svg?v=5eb58b")

                vote_count_neg = review.find("span", class_="VoteCount--neg VoteCount js-comment-votes inline-block")
                vote_count_pos = review.find("span", class_="VoteCount--pos VoteCount js-comment-votes inline-block")
                if vote_count_neg:
                    vote_value = int(vote_count_neg.text.strip())
                elif vote_count_pos:
                    vote_value = int(vote_count_pos.text.strip())
                else:
                    vote_value = 0

                model_trim = review.find("div", class_="ModelTrim")
                make_logo_img = model_trim.find("img", class_="MakeLogo__img") if model_trim else None
                make_title = make_logo_img.get("title") if make_logo_img else "No title"
                referencia_completa = model_trim.get_text(strip=True) if model_trim else "No referencia"

                match = re.match(r"(.+)\s(\d{4})(?:\s(.+))?", referencia_completa)
                referencia = match.group(1) if match.group(1) else "Sin referencia"
                modelo = match.group(2) if match.group(2) else "Sin modelo"
                especificaciones_tecnicas = match.group(3) if match.group(3) else "Sin especificaciones tecnicas"

                author_short = review.find("div", class_="AuthorShort AuthorShort--right margin-top-small")
                autor = author_short.find("a", class_="gen-avatar").get("title") if author_short else "No autor"

                if author_short:
                    author_text = author_short.get_text(strip=True)
                    if "de " in author_text:
                        pais = author_text.split("de ")[-1].split("hace")[0].strip()
                    else:
                        pais = "No país"
                else:
                    pais = "No país"

                fecha_span = review.find("span", class_="fecha")
                fecha_completa = fecha_span.get("title") if fecha_span else "No fecha"
                fecha = fecha_completa[:10] if fecha_completa != "No fecha" else "No fecha"

                opinion_sin_definir = ""
                opinion_positiva = ""
                opinion_negativa = ""

                text_blocks = review.find_all("div", class_="Text margin-top")
                if len(text_blocks) == 1:
                    opinion_sin_definir = text_blocks[0].get_text(strip=True)
                elif len(text_blocks) > 1:
                    for block in text_blocks:
                        text_content = block.get_text(strip=True)
                        if "Lo mejor:" in text_content:
                            opinion_positiva = text_content.replace("Lo mejor:", "").strip()
                        elif "Lo peor:" in text_content:
                            opinion_negativa = text_content.replace("Lo peor:", "").strip()
                        else:
                            opinion_sin_definir = text_content

                review_instance = Review(
                    modelo=modelo,
                    calificacion=star_count,
                    aceptacion=vote_value,
                    marca=make_title,
                    referencia=referencia,
                    especificaciones_tecnicas=especificaciones_tecnicas,
                    autor=autor,
                    pais=pais,
                    fecha=fecha,
                    opinion_sin_definir=opinion_sin_definir,
                    opinion_positiva=opinion_positiva,
                    opinion_negativa=opinion_negativa
                )
                review_instance.save()

        # Recuperar todos los datos nuevamente para devolverlos en la respuesta
        all_reviews = Review.objects.all()
        serializer = ReviewSerializer(all_reviews, many=True)
        return Response(serializer.data)

class BaseReviewSummaryView(APIView):
    brand_name = None
    type_opinion = None
    reference = None

    def get_reviews(self):
        if self.brand_name and self.type_opinion:
            return Review.objects.filter(marca__icontains=self.brand_name).values_list(self.type_opinion, 'calificacion')
        return []

    def get(self, request, format=None):
        # Filtrar las opiniones de la marca
        reviews = self.get_reviews()
        opinions = [review[0] for review in reviews]  # Extraer opiniones
        calificaciones = [review[1] for review in reviews if review[1] is not None]  # Obtener calificaciones

        # Calcular el promedio de calificaciones
        promedio_calificaciones = sum(calificaciones) / len(calificaciones) if calificaciones else None

        all_positives = " ".join(opinions)

        # Inicializar el tokenizer y el modelo
        tokenizer = BartTokenizer.from_pretrained('sshleifer/distilbart-cnn-12-6')
        model = BartForConditionalGeneration.from_pretrained('sshleifer/distilbart-cnn-12-6')

        # Tokenizar el texto y dividir en fragmentos
        inputs = tokenizer(all_positives, return_tensors="pt", truncation=True, max_length=1024, return_overflowing_tokens=True)
        fragment_ids = inputs['input_ids']
        attention_masks = inputs['attention_mask']

        # Generar un resumen para cada fragmento con ajustes para un texto más extenso
        summaries = []
        for i in range(len(fragment_ids)):
            summary_ids = model.generate(
                fragment_ids[i].unsqueeze(0), 
                attention_mask=attention_masks[i].unsqueeze(0),
                max_length=500,  # Aumentar longitud máxima
                min_length=300,  # Aumentar longitud mínima
                length_penalty=1.0,  # Reducir penalización de longitud
                num_beams=7,  # Aumentar el número de beams
                early_stopping=True
            )
            summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summaries.append(summary)

        # Combinar todos los resúmenes parciales
        combined_summary = " ".join(summaries)

        # Traducir sólo los fragmentos en inglés al español
        translator = Translator()
        translated_fragments = []
        for sentence in combined_summary.split('.'):
            sentence = sentence.strip()
            if len(sentence) > 0:  # Asegurarse de que el fragmento no esté vacío
                try:
                    if detect(sentence) == 'en':
                        translated_sentence = translator.translate(sentence, dest='es').text
                        translated_fragments.append(translated_sentence)
                    else:
                        translated_fragments.append(sentence)
                except LangDetectException:
                    # Si langdetect no puede identificar el idioma, dejar el fragmento como está
                    translated_fragments.append(sentence)

        # Unir los fragmentos traducidos
        translated_summary = ". ".join(translated_fragments)

        return Response({
            "resumen_opiniones": translated_summary,
            "referencia": self.reference,
            "promedio_calificaciones": promedio_calificaciones
        })


class PositiveChevroletReviews(BaseReviewSummaryView):
    brand_name = 'chevrolet'
    type_opinion = 'opinion_positiva'
    reference = 'Chevrolet Sail'

class PositiveToyotaReviews(BaseReviewSummaryView):
    brand_name = 'toyota'
    type_opinion = 'opinion_positiva'
    fixed_reference = 'Toyota Hilux'

class PositiveVolkswagenReviews(BaseReviewSummaryView):
    brand_name = 'volkswagen'
    type_opinion = 'opinion_positiva'
    fixed_reference = 'Volkswagen Gol'

class NegativeChevroletReviews(BaseReviewSummaryView):
    brand_name = 'chevrolet'
    type_opinion = 'opinion_negativa'
    reference = 'Chevrolet Sail'

class NegativeToyotaReviews(BaseReviewSummaryView):
    brand_name = 'toyota'
    type_opinion = 'opinion_negativa'
    fixed_reference = 'Toyota Hilux'

class NegativeVolkswagenReviews(BaseReviewSummaryView):
    brand_name = 'volkswagen'
    type_opinion = 'opinion_negativa'
    fixed_reference = 'Volkswagen Gol'

class NonSpecificChevroletReviews(BaseReviewSummaryView):
    brand_name = 'chevrolet'
    type_opinion = 'opinion_sin_definir'
    reference = 'Chevrolet Sail'

class NonSpecificToyotaReviews(BaseReviewSummaryView):
    brand_name = 'toyota'
    type_opinion = 'opinion_sin_definir'
    fixed_reference = 'Toyota Hilux'

class NonSpecificVolkswagenReviews(BaseReviewSummaryView):
    brand_name = 'volkswagen'
    type_opinion = 'opinion_sin_definir'
    fixed_reference = 'Volkswagen Gol'

class chevroletReviews(APIView):
    def get(self, request, format=None):
        chevrolet_reviews = Review.objects.filter(marca__icontains='chevrolet')
        serializer = ReviewSerializer(chevrolet_reviews, many=True)
        return Response(serializer.data)

class volkswagenReviews(APIView):
    def get(self, request, format=None):
        volkswagen_reviews = Review.objects.filter(marca__icontains='volkswagen')
        serializer = ReviewSerializer(volkswagen_reviews, many=True)
        return Response(serializer.data)

class toyotaReviews(APIView):
    def get(self, request, format=None):
        toyota_reviews = Review.objects.filter(marca__icontains='toyota')
        serializer = ReviewSerializer(toyota_reviews, many=True)
        return Response(serializer.data)