# Pydantic Textract



## How to run via FastAPI

* `pip install -r requirements.txt` (ideally in a virtualenv of some sort)
* `mv env.example .env` to create a `.env` file to house the secrets 
* Update the `.env` with your secrets
* uvicorn main:app --reload

## Making An API Call via Postman/cURL

```sh
curl -X 'POST' \
  'https://localhost:8000/process_document/CFM%20Processing' \
  -H 'accept: application/json' \
  -H 'Authorization: brandmuscle' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@MARKIE-Bobcat Tutorial Content-220424-155942.pdf;type=application/pdf'
```

### Example Response

```json
{
  "vendor_merchant_name": "Omniclectic",
  "bill_invoice_amount": "$104.00",
  "requested_amount": "$104.00",
  "date_of_invoice": "Jun 9, 2023",
  "claim_start_date": "Jun 9, 2023",
  "claim_end_date": "Jun 9, 2023",
  "media_type": "Unknown",
  "activity_type": "Unknown",
  "comments": "Invoice #1066. Item: Kind of Yellow boop! cap - $92.00, handmade artisan keycap. Shipping: $12.00. Total: $104.00. Seller note: While I try to uphold a high standard for quality control, sometimes flaws slip through. If you find your cap to be damaged or unacceptable in any way, please don't hesitate to reach out at comniclectic@gmail.com. Thanks so much for your support!",
  "description": "Handmade artisan keycap purchase.",
  "account_id_number": "Unknown",
  "invoice": "Unknown"
}
```

### .env example

```
aws_region_name=your_aws_region_name
aws_access_key_id=your_aws_access_key_id
aws_secret_access_key=your_aws_secret_access_key
openai_api=your_openai_api_key
password=your_password
```
