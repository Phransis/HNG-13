import random
import requests
from django.http import JsonResponse, FileResponse
from django.utils.timezone import now
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import Country
import os
from PIL import Image, ImageDraw, ImageFont

@csrf_exempt
def refresh_countries(request):
	try:
		countries_resp = requests.get(
			"https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies",
			timeout=10,
		)
		exchange_resp = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)

		if countries_resp.status_code != 200 or exchange_resp.status_code != 200:
			return JsonResponse(
				{
					"error": "External data source unavailable",
					"details": "Could not fetch data from restcountries.com or open.er-api.com",
				},
				status=503,
			)

		countries_data = countries_resp.json()
		exchange_rates = exchange_resp.json().get("rates", {})

		for c in countries_data:
			name = c.get("name")
			population = c.get("population", 0)
			currencies = c.get("currencies", [])
			region = c.get("region")
			capital = c.get("capital")
			flag_url = c.get("flag")

			if not name or not population:
				continue

			currency_code = None
			if currencies and isinstance(currencies, list) and len(currencies) > 0:
				currency_code = currencies[0].get("code")

			exchange_rate = exchange_rates.get(currency_code) if currency_code else None

			if exchange_rate:
				gdp_multiplier = random.randint(1000, 2000)
				estimated_gdp = (population * gdp_multiplier) / exchange_rate
			else:
				estimated_gdp = 0

			Country.objects.update_or_create(
				name__iexact=name,
				defaults={
					"name": name,
					"capital": capital,
					"region": region,
					"population": population,
					"currency_code": currency_code,
					"exchange_rate": exchange_rate,
					"estimated_gdp": estimated_gdp,
					"flag_url": flag_url,
					"last_refreshed_at": now(),
				},
			)

		# Generate summary image
		generate_summary_image()

		return JsonResponse({"message": "Countries refreshed successfully"}, status=200)

	except requests.RequestException:
		return JsonResponse(
			{
				"error": "External data source unavailable",
				"details": "Network error while fetching data",
			},
			status=503,
		)

def generate_summary_image():
	top_countries = Country.objects.order_by("-estimated_gdp")[:5]
	total = Country.objects.count()
	timestamp = now().strftime("%Y-%m-%d %H:%M:%S")

	image = Image.new("RGB", (600, 400), color=(240, 240, 240))
	draw = ImageDraw.Draw(image)

	title_font = ImageFont.load_default()
	draw.text((20, 20), f"Total Countries: {total}", fill=(0, 0, 0), font=title_font)
	draw.text((20, 50), f"Last Refresh: {timestamp}", fill=(0, 0, 0), font=title_font)

	y_offset = 100
	draw.text((20, y_offset - 20), "Top 5 by GDP:", fill=(0, 0, 0), font=title_font)

	for i, c in enumerate(top_countries, start=1):
		draw.text(
			(20, y_offset + i * 25),
			f"{i}. {c.name} - {round(c.estimated_gdp, 2)}",
			fill=(0, 0, 0),
			font=title_font,
		)

	os.makedirs(os.path.join(settings.BASE_DIR, "cache"), exist_ok=True)
	image.save(os.path.join(settings.BASE_DIR, "cache/summary.png"))

def get_countries(request):
	region = request.GET.get("region")
	currency = request.GET.get("currency")
	sort = request.GET.get("sort")

	qs = Country.objects.all()

	if region:
		qs = qs.filter(region__iexact=region)
	if currency:
		qs = qs.filter(currency_code__iexact=currency)

	if sort == "gdp_desc":
		qs = qs.order_by("-estimated_gdp")

	data = [
		{
			"id": c.id,
			"name": c.name,
			"capital": c.capital,
			"region": c.region,
			"population": c.population,
			"currency_code": c.currency_code,
			"exchange_rate": c.exchange_rate,
			"estimated_gdp": c.estimated_gdp,
			"flag_url": c.flag_url,
			"last_refreshed_at": c.last_refreshed_at,
		}
		for c in qs
	]

	return JsonResponse(data, safe=False)


def get_country(request, name):
	try:
		c = Country.objects.get(name__iexact=name)
		return JsonResponse(
			{
				"id": c.id,
				"name": c.name,
				"capital": c.capital,
				"region": c.region,
				"population": c.population,
				"currency_code": c.currency_code,
				"exchange_rate": c.exchange_rate,
				"estimated_gdp": c.estimated_gdp,
				"flag_url": c.flag_url,
				"last_refreshed_at": c.last_refreshed_at,
			}
		)
	except Country.DoesNotExist:
		return JsonResponse({"error": "Country not found"}, status=404)


@csrf_exempt
def delete_country(request, name):
	try:
		c = Country.objects.get(name__iexact=name)
		c.delete()
		return JsonResponse({}, status=204)
	except Country.DoesNotExist:
		return JsonResponse({"error": "Country not found"}, status=404)


def get_status(request):
	total = Country.objects.count()
	last_refreshed = Country.objects.order_by("-last_refreshed_at").first()
	ts = last_refreshed.last_refreshed_at if last_refreshed else None
	return JsonResponse({
		"total_countries": total,
		"last_refreshed_at": ts,
	})


def get_summary_image(request):
	image_path = os.path.join(settings.BASE_DIR, "cache/summary.png")
	if not os.path.exists(image_path):
		return JsonResponse({"error": "Summary image not found"}, status=404)
	return FileResponse(open(image_path, "rb"), content_type="image/png")