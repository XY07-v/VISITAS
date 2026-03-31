import os
from flask import Flask, render_template_string, request
from pymongo import MongoClient

app = Flask(__name__)

# --- CONEXIÓN ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- HTML INTEGRADO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Panel NestleDB</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; padding: 20px; }
        .img-visit { width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 1px solid #ddd; }
        .card-table { background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); padding: 20px; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <h2 class="text-center mb-4">🚀 Panel de Control NestleDB</h2>
        
        <div class="card-table">
            <form method="GET" class="row g-3 mb-4">
                <div class="col-auto">
                    <input type="text" name="fecha" class="form-control" placeholder="Filtrar por fecha" value="{{ fecha_query }}">
                </div>
                <div class="col-auto">
                    <button type="submit" class="btn btn-primary">Consultar</button>
                </div>
                <div class="col-auto">
                    <a href="/" class="btn btn-outline-secondary">Limpiar</a>
                </div>
            </form>

            <table class="table table-hover align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>Fecha</th>
                        <th>Mes</th>
                        <th>Estado</th>
                        <th>BMB</th>
                        <th>Fachada</th>
                        <th>Mapa</th>
                    </tr>
                </thead>
                <tbody>
                    {% for v in visitas %}
                    <tr>
                        <td><strong>{{ v.fecha }}</strong></td>
                        <td>{{ v.MES }}</td>
                        <td>
                            {% if v.estado == -1 or v.VALOR == -1 %}
                                <span class="badge bg-success">✅ Positivo</span>
                            {% else %}
                                <span class="badge bg-danger">❌ Déficit</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if v.f_bmb %}
                                <a href="{{ v.f_bmb }}" target="_blank"><img src="{{ v.f_bmb }}" class="img-visit"></a>
                            {% else %} <small>N/A</small> {% endif %}
                        </td>
                        <td>
                            {% if v.f_fachada %}
                                <a href="{{ v.f_fachada }}" target="_blank"><img src="{{ v.f_fachada }}" class="img-visit"></a>
                            {% else %} <small>N/A</small> {% endif %}
                        </td>
                        <td>
                            {% if v.gps %}
                                <a href="https://www.google.com/maps/search/?api=1&query={{ v.gps }}" target="_blank" class="btn btn-sm btn-info text-white">📍 Ver</a>
                            {% else %} <small>N/A</small> {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    fecha_query = request.args.get('fecha', '')
    query = {"fecha": fecha_query} if fecha_query else {}
    try:
        datos = list(visitas_col.find(query).sort("fecha", -1).limit(50))
        return render_template_string(HTML_TEMPLATE, visitas=datos, fecha_query=fecha_query)
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
