from django.shortcuts import render
from products.models import ProductPrice, Product, GiftCard
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
import datetime

# Create your views here.

class ProductPriceView(APIView):
	# We want to accept post requests with JSON content only
	parser_classes = (JSONParser,)

	def post(self, request, format=None):
		# Capture the JSON data received as post:
		json_data = request.data

		# msg will hold any messages for problems detected with the received data
		msg = None

		try:
			if "productCode" and "date" in json_data.keys():
				# Go ahead and process the information
				# Make date usable
				date_str = json_data['date']
				format_str = "%m-%d-%Y"
				date_obj = datetime.datetime.strptime(date_str, format_str)

				# Figure out the productCode
				prod = Product.objects.get(code=json_data["productCode"])

				# Now work with ProductPrice for the special offers
				prod_price = ProductPrice.objects.filter(product=prod)

				# Will determine the price with three cases: thanksgiving, 2019 date or none of them

				price = 0

				# First, thanksgiving
				prod_price_tg = prod_price.exclude(date_end=None).filter(date_start__lte=date_obj,date_end__gte=date_obj)
				if len(prod_price_tg) == 1:
					price = prod_price_tg[0].price

				# Now Jan 1, 2019 and older
				prod_price_ny = prod_price.filter(date_end=None).filter(date_start__lte=date_obj)
				if len(prod_price_ny) == 1:
					price = prod_price_ny[0].price

				# If none of the above, use the product price:
				if len(prod_price_tg) == 0 and len(prod_price_ny) == 0:
					price = prod.price

				# Capture gift card information, if received
				if "giftCardCode" in json_data.keys():
					gift_amt = 0
					
					gift_code = json_data['giftCardCode']

					try:
						gift_obj = GiftCard.objects.get(code=gift_code)
						# If the start date is less than the provided date
						if gift_obj.date_start <= date_obj.date():
							# If there is no end date, or if the date received is less than the date_end for this gift card
							if (not gift_obj.date_end) or (gift_obj.date_end and gift_obj.date_end >= date_obj.date()):
								gift_amt = gift_obj.amount
					except:
						# Do nothing: the gift card code is invalid
						# Keep a message to report later
						msg = "Optional giftCardCode provided is invalid"
						pass

					# Adjust the price if the gift card code is valid and current/usable
					price = price - gift_amt
					if price <= 0:
						price = 0

				# Prepare a nicely formatted final price
				price_str = '${0:.2f}'.format(price / 100)

				if msg:
					return Response({'success':'yes', 'price': price_str, 'message': msg})
				else:
					return Response({'success':'yes', 'price': price_str})
			else:
				msg = "Need at a minimum valid date (mm-dd-YYYY) and productCode in JSON format"
				return Response({'success':'no', 'received data': json_data, 'message': msg})

		except Exception as e:
			# Return information on the actual exception caught
			msg = "Exception ocurred: {}".format(e)
			return Response({'success':'no', 'received data': json_data, 'message': msg})
		