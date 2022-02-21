## Postgres
docker run --name lurnby-postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres

## Lurnby
docker run --name lurnby -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
    --link lurnby-postgres:dbserver \
    --mount type=bind,source=./certs,target=/certs \
    lurnby:latest


     
     