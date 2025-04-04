gcloud functions deploy investment_bank_crawler \
--gen2 \
--runtime=python311 \
--region=asia-east1 \
--source=./crawler/investment_bank \
--entry-point=run \
--allow-unauthenticated \
--trigger-bucket=ib_report_v1 \
--env-vars-file=./crawler/investment_bank/configs/.env.yaml \
--serve-all-traffic-latest-revision \
--memory=512MB \
--max-instances=10
