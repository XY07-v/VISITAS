import os
from flask import Flask, render_template_string, request
from pymongo import MongoClient

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- PLANTILLA HTML OPTIMIZADA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NestleDB - Reporte Completo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .main-container { padding: 15px; max-width: 1400px; margin: auto; }
        .table-card { 
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 8px 30px rgba(0,0,0,0.1); 
            overflow: hidden;
            margin-top: 20px;
        }
        
        /* Imágenes */
        .img-preview { 
            width: 80px; height: 80px; object-fit: cover; 
            border-radius: 8px; cursor: pointer; border: 1px solid #dee2e6;
            transition: transform 0.2s;
        }
        .img-preview:hover { transform: scale(1.05); }
        
        /* Celdas con datos completos */
        .table td, .table th { 
            vertical-align: middle; 
            white-space: normal; /* Asegura que el texto no se corte y baje al siguiente renglón */
            word-wrap: break-word;
            min-width: 100px;
        }

        /* Modales */
        .modal-content { border-radius: 15px; overflow: hidden; }
        #modalImg { width: 100%; height: auto; }
        iframe { width: 100%; height: 75vh; border: 0; }

        .search-box { border-radius: 25px; padding-left: 20px; border: 2px solid #0d6efd; }
        .btn-custom { border-radius: 25px; padding: 10px 25px; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="text-center mb-4">
            <h2 class="fw-bold text-primary">📊 Panel de Visitas Nestle</h2>
        </div>
        
        <div class="card border-0 shadow-sm p-4 mb-4" style="border-radius: 15px;">
            <form method="GET" class="row g-3 justify-content-center">
                <div class="col-md-3">
                    <label class="form-label small fw-bold">Fecha (AAAA-MM-DD):</label>
                    <input type="text" name="fecha" class="form-control search-box" placeholder="Ej: 2026-03-31" value="{{ f_val }}">
                </div>
                <div class="col-md-5">
                    <label class="form-label small fw-bold">Buscar (PV, BMB o Usuario):</label>
                    <input type="text" name="busqueda" class="form-control search-box" placeholder="Escriba PV, nombre de BMB o Usuario..." value="{{ b_val }}">
                </div>
                <div class="col-md-auto d-flex align-items-end gap-2">
                    <button type="submit" class="btn btn-primary btn-custom shadow">🔍 Buscar</button>
                    <a href="/" class="btn btn-outline-secondary btn-custom">🔄 Limpiar</a>
                </div>
            </form>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table class="table table-striped table-hover mb-0">
                    <thead class="table-primary text-uppercase small">
                        <tr>
                            <th>Fecha</th>
                            <th>Usuario</th>
                            <th>PV</th>
                            <th>BMB (Datos)</th>
                            <th>Foto BMB</th>
                            <th>Foto Fachada</th>
                            <th>GPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in visitas %}
                        <tr>
                            <td class="fw-bold text-nowrap">{{ v.fecha_limpia }}</td>
                            <td>{{ v.usuario }}</td>
                            <td><span class="badge bg-light text-dark border">{{ v.pv }}</span></td>
                            <td>{{ v.bmb }}</td>
                            <td>
                                {% if v.f_bmb %}
                                    <img src="{{ v.f_bmb }}" class="img-preview shadow-sm" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_bmb }}')">
                                {% else %} <span class="text-muted small italic">Sin foto</span> {% endif %}
                            </td>
                            <td>
                                {% if v.f_fachada %}
                                    <img src="{{ v.f_fachada }}" class="img-preview shadow-sm" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_fachada }}')">
                                {% else %} <span class="text-muted small italic">Sin foto</span> {% endif %}
                            </td>
                            <td>
                                {% if v.gps %}
                                    <button class="btn btn-sm btn-danger rounded-pill px-3 shadow-sm" data-bs-toggle="modal" data-bs-target="#mapModal" onclick="showMap('{{ v.gps }}')">📍 Mapa</button>
                                {% else %} <span class="text-muted">---</span> {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="imgModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content">
                <div class="modal-body p-1 text-center bg-dark">
                    <img id="modalImg" src="">
                    <button type="button" class="btn btn-light mt-2 mb-2" data-bs-dismiss="modal">Cerrar</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="mapModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-fullscreen-md-down modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header bg-danger text-white">
                    <h6 class="modal-title fw-bold">📍 Ubicación del Punto</h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-0">
                    <iframe id="mapFrame" src=""></iframe>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showImg(url) {
            document.getElementById('modalImg').src = url;
        }
        function showMap(coords) {
            const url = `https://maps.google.com/maps?q=${coords}&t=&z=15&ie=UTF8&iwloc=&output=embed`;
            document.getElementById('mapFrame').src = url;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    f_val = request.args.get('fecha', '')
    b_val = request.args.get('busqueda', '')

    # Construcción del Filtro
    query = {}
    
    # Filtro de fecha exacto o parcial
    if f_val:
        query['fecha'] = {"$regex": f_val}
    
    # Filtro global para PV, BMB y Usuario
    if b_val:
        query["$or"] = [
            {"pv": {"$regex": b_val, "$options": "i"}},
            {"bmb": {"$regex": b_val, "$options": "i"}},
            {"usuario": {"$regex": b_val, "$options": "i"}}
        ]

    try:
        raw_datos = list(visitas_col.find(query).sort("fecha", -1))
        
        # Procesamiento de fecha limpia (AAAA-MM-DD)
        for item in raw_datos:
            f = str(item.get('fecha', ''))
            item['fecha_limpia'] = f[:10] if len(f) >= 10 else f

        return render_template_string(HTML_TEMPLATE, visitas=raw_datos, f_val=f_val, b_val=b_val)
    except Exception as e:
        return f"Error de conexión: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
