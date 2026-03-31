import os
import json
from flask import Flask, render_template_string, request
from pymongo import MongoClient
from bson import json_util

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- PLANTILLA HTML (INTERACTIVA) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NestleDB - Detalle Expandido</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; font-family: 'Segoe UI', sans-serif; }
        .main-container { padding: 10px; max-width: 1000px; margin: auto; }
        .table-card { background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
        
        /* Botones de PV y BMB */
        .btn-detail { 
            background: none; border: none; color: #0d6efd; 
            text-decoration: underline; font-weight: bold; padding: 0;
            text-align: left;
        }
        .btn-detail:hover { color: #0a58ca; }

        /* Estilos del Modal de Detalles */
        .detail-item { border-bottom: 1px solid #eee; padding: 8px 0; }
        .detail-label { font-weight: bold; color: #555; font-size: 0.85rem; text-transform: uppercase; }
        .detail-value { color: #000; word-break: break-all; }
        
        .img-full { width: 100%; border-radius: 10px; margin-top: 10px; border: 1px solid #ddd; }
        iframe { width: 100%; height: 350px; border: 0; border-radius: 10px; }
        
        .search-bar { border-radius: 20px; border: 2px solid #dee2e6; transition: 0.3s; }
        .search-bar:focus { border-color: #0d6efd; box-shadow: none; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="text-center py-3">
            <h4 class="fw-bold">📱 NestleDB - Visitas</h4>
        </div>

        <div class="card border-0 shadow-sm p-3 mb-3" style="border-radius: 15px;">
            <form method="GET" class="row g-2">
                <div class="col-12">
                    <input type="text" name="busqueda" class="form-control search-bar" 
                           placeholder="Buscar por PV, BMB o Usuario..." value="{{ b_val }}">
                </div>
                <div class="col-6">
                    <button type="submit" class="btn btn-primary w-100 rounded-pill">🔍 Buscar</button>
                </div>
                <div class="col-6">
                    <a href="/" class="btn btn-light w-100 rounded-pill border">🔄 Limpiar</a>
                </div>
            </form>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-dark">
                        <tr>
                            <th>Fecha</th>
                            <th>PV / BMB (Ver Detalle)</th>
                            <th>GPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in visitas %}
                        <tr>
                            <td class="small fw-bold text-nowrap">{{ v.fecha_limpia }}</td>
                            <td>
                                <button class="btn-detail" onclick='verDetalles({{ v.json_data | safe }})'>
                                    PV: {{ v.pv }} <br>
                                    <span class="text-muted small">BMB: {{ v.bmb }}</span>
                                </button>
                            </td>
                            <td>
                                {% if v.gps %}
                                    <button class="btn btn-sm btn-danger rounded-circle" 
                                            onclick="verMapa('{{ v.gps }}')">📍</button>
                                {% else %} --- {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="detallesModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
            <div class="modal-content" style="border-radius: 20px;">
                <div class="modal-header bg-primary text-white">
                    <h6 class="modal-title fw-bold">Detalles Completos del Registro</h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="contenidoDetalles">
                        </div>
                    
                    <hr>
                    <div class="row">
                        <div class="col-6">
                            <p class="fw-bold small mb-1">FOTO BMB:</p>
                            <div id="fotoBMB"></div>
                        </div>
                        <div class="col-6">
                            <p class="fw-bold small mb-1">FOTO FACHADA:</p>
                            <div id="fotoFachada"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="mapModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h6 class="modal-title">📍 Ubicación Exacta</h6>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-0">
                    <iframe id="mapFrame" src=""></iframe>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const mDetalles = new bootstrap.Modal(document.getElementById('detallesModal'));
        const mMapa = new bootstrap.Modal(document.getElementById('mapModal'));

        function verDetalles(data) {
            let html = "";
            // Recorremos todas las llaves del registro para no dejar nada por fuera
            for (let key in data) {
                if (!key.startsWith('f_') && key !== '_id' && key !== 'json_data' && key !== 'fecha_limpia') {
                    html += `
                        <div class="detail-item">
                            <div class="detail-label">${key}</div>
                            <div class="detail-value">${data[key] || '---'}</div>
                        </div>
                    `;
                }
            }
            document.getElementById('contenidoDetalles').innerHTML = html;
            
            // Mostrar fotos si existen
            document.getElementById('fotoBMB').innerHTML = data.f_bmb ? `<img src="${data.f_bmb}" class="img-full">` : '<small>No disponible</small>';
            document.getElementById('fotoFachada').innerHTML = data.f_fachada ? `<img src="${data.f_fachada}" class="img-full">` : '<small>No disponible</small>';
            
            mDetalles.show();
        }

        function verMapa(coords) {
            const url = `https://maps.google.com/maps?q=${coords}&t=&z=16&ie=UTF8&iwloc=&output=embed`;
            document.getElementById('mapFrame').src = url;
            mMapa.show();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    b_val = request.args.get('busqueda', '')

    query = {}
    if b_val:
        query["$or"] = [
            {"pv": {"$regex": b_val, "$options": "i"}},
            {"bmb": {"$regex": b_val, "$options": "i"}},
            {"usuario": {"$regex": b_val, "$options": "i"}},
            {"fecha": {"$regex": b_val}}
        ]

    try:
        raw_datos = list(visitas_col.find(query).sort("fecha", -1))
        
        for item in raw_datos:
            # Limpiar fecha
            f = str(item.get('fecha', ''))
            item['fecha_limpia'] = f[:10] if len(f) >= 10 else f
            
            # Convertir todo el registro a JSON para que JS lo lea al hacer click
            # Esto permite ver CUALQUIER columna nueva sin cambiar el código
            item['json_data'] = json_util.dumps(item)

        return render_template_string(HTML_TEMPLATE, visitas=raw_datos, b_val=b_val)
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
