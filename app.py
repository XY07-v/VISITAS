import os
from flask import Flask, render_template_string, request
from pymongo import MongoClient

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- PLANTILLA HTML CON MODALES Y FILTROS ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel NestleDB - Full</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; font-size: 0.9rem; }
        .img-preview { width: 60px; height: 60px; object-fit: cover; border-radius: 5px; cursor: pointer; border: 1px solid #ddd; }
        .table-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 1.5rem; }
        .modal-body img { width: 100%; border-radius: 8px; }
        iframe { width: 100%; height: 400px; border: 0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <h3 class="text-center mb-4 text-primary fw-bold">🚀 Sistema de Gestión NestleDB</h3>
        
        <div class="table-card">
            <form method="GET" class="row g-2 mb-4">
                <div class="col-md-3">
                    <input type="text" name="fecha" class="form-control" placeholder="Filtrar por Fecha" value="{{ f_val }}">
                </div>
                <div class="col-md-3">
                    <input type="text" name="usuario" class="form-control" placeholder="Filtrar por Usuario" value="{{ u_val }}">
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-primary w-100">Aplicar Filtros</button>
                </div>
                <div class="col-md-1">
                    <a href="/" class="btn btn-outline-secondary w-100">🔄</a>
                </div>
            </form>

            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th>Fecha</th>
                            <th>Usuario</th>
                            <th>Mes</th>
                            <th>Estado</th>
                            <th>Foto BMB</th>
                            <th>Foto Fachada</th>
                            <th>GPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in visitas %}
                        <tr>
                            <td class="fw-bold">{{ v.fecha }}</td>
                            <td><span class="badge bg-info text-dark">{{ v.usuario }}</span></td>
                            <td>{{ v.MES }}</td>
                            <td>
                                {% if v.estado == -1 or v.VALOR == -1 %}
                                    <span class="text-success fw-bold">✔ Positivo</span>
                                {% else %}
                                    <span class="text-danger fw-bold">✘ Déficit</span>
                                {% endif %}
                            </td>
                            <td>
                                {% if v.f_bmb %}
                                    <img src="{{ v.f_bmb }}" class="img-preview" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_bmb }}', 'BMB')">
                                {% else %} <small class="text-muted">N/A</small> {% endif %}
                            </td>
                            <td>
                                {% if v.f_fachada %}
                                    <img src="{{ v.f_fachada }}" class="img-preview" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_fachada }}', 'Fachada')">
                                {% else %} <small class="text-muted">N/A</small> {% endif %}
                            </td>
                            <td>
                                {% if v.gps %}
                                    <button class="btn btn-sm btn-outline-danger" data-bs-toggle="modal" data-bs-target="#mapModal" onclick="showMap('{{ v.gps }}')">📍 Ver Mapa</button>
                                {% else %} <small class="text-muted">S/N</small> {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="imgModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="imgTitle">Visualización de Foto</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-center">
                    <img id="modalImg" src="" alt="Cargando...">
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="mapModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header text-white bg-danger">
                    <h5 class="modal-title">📍 Ubicación del Punto</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <iframe id="mapFrame" src=""></iframe>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showImg(url, title) {
            document.getElementById('modalImg').src = url;
            document.getElementById('imgTitle').innerText = 'Foto: ' + title;
        }
        function showMap(coords) {
            // Genera el link embebido de Google Maps
            const url = `https://maps.google.com/maps?q=${coords}&t=&z=15&ie=UTF8&iwloc=&output=embed`;
            document.getElementById('mapFrame').src = url;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Obtener parámetros de búsqueda
    f_val = request.args.get('fecha', '')
    u_val = request.args.get('usuario', '')

    # Construir el filtro para MongoDB
    query = {}
    if f_val: query['fecha'] = f_val
    if u_val: query['usuario'] = u_val

    try:
        # Traer todos los datos que coincidan (quitamos el .limit para ver todo)
        datos = list(visitas_col.find(query).sort("fecha", -1))
        return render_template_string(HTML_TEMPLATE, visitas=datos, f_val=f_val, u_val=u_val)
    except Exception as e:
        return f"<h3>Error:</h3> {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
