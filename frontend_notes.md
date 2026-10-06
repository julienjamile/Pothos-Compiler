To use #frontend, expose /dist/* to `http://ip-address/`,
    handle `http://ip-address/api.json` GET/POST request. Use format given inside ./api,json
        GET -> frontend receives lexer result
        POST -> Backend receives user code.
            Adjust frontend code freely, bundle frontend code using `npm run build`.
            AI Generated python flask environment for demo only. Test using .venv/bin/python app.py

To update frontend, run 'npm install' first to retrieve dependencies.