import os
from flask import Flask, render_template_string, request
from pymongo import MongoClient

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- PLANTILLA HTML RESPONSIVA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NestleDB - Mobile Ready</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #eff2f5; font-family: sans-serif; }
        .main-container { padding: 10px; max-width: 1200px; margin: auto; }
        .table-card { background: white; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }
        
        /* Ajuste de imágenes para móviles */
        .img-preview { 
            width: 70px; height: 70px; object-fit: cover; 
            border-radius: 10px; cursor: pointer; border: 2px solid #fff; shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        /* Forzar que la tabla no rompa el diseño en móvil */
        .table responsive { font-size: 0.85rem; }
        
        /* Ajuste de los modales */
        .modal-content { border-radius: 20px; border: none; }
        #modalImg { width: 100%; height: auto; border-radius: 10px; }
        iframe { width: 100%; height: 70vh; border: 0; border-radius: 10px; }

        .btn-filter { border-radius: 10px; height: 45px; }
        input.form-control { border-radius: 10px; height: 45px; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="text-center py-3">
            <h4 class="fw-bold text-dark">📊 Gestión NestleDB</h4>
            <p class="text-muted small">Vista optimizada para Móvil y Desktop</p>
        </div>
        
        <div class="card border-0 shadow-sm mb-3 p-3" style="border-radius: 15px;">
            <form method="GET" class="row g-2">
                <div class="col-6 col-md-4">
                    <input type="text" name="fecha" class="form-control" placeholder="Fecha (AAAA-MM-DD)" value="{{ f_val }}">
                </div>
                <div class="col-6 col-md-4">
                    <input type="text" name="usuario" class="form-control" placeholder="Usuario" value="{{ u_val }}">
                </div>
                <div class="col-12 col-md-4">
                    <div class="d-flex gap-2">
                        <button type="submit" class="btn btn-primary btn-filter w-100">Filtrar</button>
                        <a href="/" class="btn btn-light btn-filter border">🔄</a>
                    </div>
                </div>
            </form>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-light">
                        <tr>
                            <th>Fecha</th>
                            <th>Usuario</th>
                            <th>BMB</th>
                            <th>Fachada</th>
                            <th>GPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in visitas %}
                        <tr>
                            <td class="text-nowrap fw-bold">{{ v.fecha_limpia }}</td>
                            <td><span class="text-truncate d-inline-block" style="max-width: 80px;">{{ v.usuario }}</span></td>
                            <td>
                                {% if v.f_bmb %}
                                    <img src="{{ v.f_bmb }}" class="img-preview shadow-sm" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_bmb }}', 'BMB')">
                                {% else %} --- {% endif %}
                            </td>
                            <td>
                                {% if v.f_fachada %}
                                    <img src="{{ v.f_fachada }}" class="img-preview shadow-sm" data-bs-toggle="modal" data-bs-target="#imgModal" onclick="showImg('{{ v.f_fachada }}', 'Fachada')">
                                {% else %} --- {% endif %}
                            </td>
                            <td>
                                {% if v.gps %}
                                    <button class="btn btn-sm btn-danger rounded-pill px-3" data-bs-toggle="modal" data-bs-target="#mapModal" onclick="showMap('{{ v.gps }}')">📍</button>
                                {% else %} --- {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="imgModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-body p-1">
                    <img id="modalImg" src="">
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="mapModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-fullscreen-sm-down modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h6 class="modal-title fw-bold">Ubicación GPS</h6>
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
        function showImg(url, title) {
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
    u_val = request.args.get('usuario', '')

    query = {}
    if f_val: query['fecha'] = {"$regex": f_val} # Búsqueda parcial por si acaso
    if u_val: query['usuario'] = u_val

    try:
        raw_datos = list(visitas_col.find(query).sort("fecha", -1))
        
        # PROCESAMIENTO DE FECHA: Cortar para dejar solo AAAA-MM-DD
        for item in raw_datos:
            original_fecha = str(item.get('fecha', ''))
            # Si la fecha tiene más de 10 caracteres (incluye hora), la cortamos
            item['fecha_limpia'] = original_fecha[:10] if len(original_fecha) >= 10 else original_fecha

        return render_template_string(HTML_TEMPLATE, visitas=raw_datos, f_val=f_val, u_val=u_val)
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
