import os
import json
import csv
import io
from flask import Flask, render_template_string, request, make_response
from pymongo import MongoClient
from bson import json_util, ObjectId

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

# --- PLANTILLA HTML ACTUALIZADA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NestleDB - Reporte Dinámico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
        .main-container { padding: 20px; max-width: 1100px; margin: auto; }
        .table-card { background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); overflow: hidden; }
        .btn-detail { background: none; border: none; color: #0d6efd; text-decoration: underline; font-weight: bold; padding: 0; text-align: left; }
        .img-full { width: 100%; border-radius: 10px; margin-top: 10px; border: 1px solid #ddd; }
        iframe { width: 100%; height: 350px; border: 0; border-radius: 10px; }
        .filter-panel { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; border: 1px solid #e0e0e0; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="text-center mb-4">
            <h3 class="fw-bold text-primary">📊 Reporte de Visitas Nestle</h3>
        </div>

        <div class="filter-panel shadow-sm">
            <form method="GET" action="/" class="row g-3">
                <div class="col-md-4">
                    <label class="form-label small fw-bold">Búsqueda General</label>
                    <input type="text" name="busqueda" class="form-control rounded-pill" placeholder="PV, BMB, Usuario..." value="{{ b_val }}">
                </div>
                <div class="col-md-3">
                    <label class="form-label small fw-bold">Desde</label>
                    <input type="date" name="fecha_inicio" class="form-control rounded-pill" value="{{ f_inicio }}">
                </div>
                <div class="col-md-3">
                    <label class="form-label small fw-bold">Hasta</label>
                    <input type="date" name="fecha_fin" class="form-control rounded-pill" value="{{ f_fin }}">
                </div>
                <div class="col-md-2 d-flex align-items-end gap-2">
                    <button type="submit" class="btn btn-primary w-100 rounded-pill">Consultar</button>
                </div>
                <div class="col-12 mt-3 d-flex justify-content-between">
                    <a href="/" class="btn btn-sm btn-light border rounded-pill px-3">Limpiar Filtros</a>
                    <button type="submit" name="descargar" value="1" class="btn btn-sm btn-success rounded-pill px-4">📥 Descargar CSV (Filtro Actual)</button>
                </div>
            </form>
        </div>

        <div class="table-card">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="table-dark">
                        <tr>
                            <th>Fecha</th>
                            <th>PV / BMB</th>
                            <th>Usuario</th>
                            <th>GPS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in visitas %}
                        <tr>
                            <td class="small fw-bold">{{ v.fecha_limpia }}</td>
                            <td>
                                <button class="btn-detail" onclick='verDetalles({{ v.json_data | safe }})'>
                                    {{ v.pv }} <br>
                                    <span class="text-muted small">BMB: {{ v.bmb }}</span>
                                </button>
                            </td>
                            <td class="small">{{ v.usuario }}</td>
                            <td>
                                {% if v.gps %}
                                    <button class="btn btn-sm btn-outline-danger rounded-circle" onclick="verMapa('{{ v.gps }}')">📍</button>
                                {% else %} --- {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                        {% if not visitas %}
                        <tr><td colspan="4" class="text-center py-4 text-muted">No se encontraron registros para este periodo.</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="detallesModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
            <div class="modal-content" style="border-radius: 20px;">
                <div class="modal-header bg-primary text-white">
                    <h6 class="modal-title fw-bold">Detalle del Registro</h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="contenidoDetalles"></div>
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
        <div class="modal-dialog modal-dialog-centered"><div class="modal-content">
            <div class="modal-header"><h6>Ubicación</h6><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <div class="modal-body p-0"><iframe id="mapFrame" src=""></iframe></div>
        </div></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const mDetalles = new bootstrap.Modal(document.getElementById('detallesModal'));
        const mMapa = new bootstrap.Modal(document.getElementById('mapModal'));

        function verDetalles(data) {
            let html = "";
            for (let key in data) {
                if (!key.startsWith('f_') && !['_id', 'json_data', 'fecha_limpia'].includes(key)) {
                    html += `<div class="p-2 border-bottom"><span class="fw-bold text-uppercase small text-muted">${key}:</span> <span class="ms-2">${data[key] || '---'}</span></div>`;
                }
            }
            document.getElementById('contenidoDetalles').innerHTML = html;
            document.getElementById('fotoBMB').innerHTML = data.f_bmb ? `<img src="${data.f_bmb}" class="img-full">` : '<small>Sin foto</small>';
            document.getElementById('fotoFachada').innerHTML = data.f_fachada ? `<img src="${data.f_fachada}" class="img-full">` : '<small>Sin foto</small>';
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
    f_inicio = request.args.get('fecha_inicio', '')
    f_fin = request.args.get('fecha_fin', '')
    descargar = request.args.get('descargar', '')

    # 1. Construcción de Query Dinámica
    query = {}
    
    # Filtro de Texto (Búsqueda en varias columnas)
    if b_val:
        query["$or"] = [
            {"pv": {"$regex": b_val, "$options": "i"}},
            {"bmb": {"$regex": b_val, "$options": "i"}},
            {"usuario": {"$regex": b_val, "$options": "i"}}
        ]
    
    # Filtro de Fecha (Rango)
    if f_inicio or f_fin:
        date_filter = {}
        if f_inicio: date_filter["$gte"] = f_inicio
        if f_fin:    date_filter["$lte"] = f_fin
        query["fecha"] = date_filter

    try:
        # 2. Ejecutar Consulta
        cursor = visitas_col.find(query).sort("fecha", -1)
        
        if descargar == "1":
            # --- LÓGICA DE DESCARGA CSV ---
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Obtener cabeceras (todas las que existan en el primer documento)
            primer_doc = visitas_col.find_one(query)
            if not primer_doc: return "No hay datos para descargar"
            
            headers = [k for k in primer_doc.keys() if k != 'json_data' and not k.startswith('f_')]
            writer.writerow(headers)
            
            for doc in cursor:
                writer.writerow([doc.get(h, "") for h in headers])
            
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers["Content-Disposition"] = f"attachment; filename=reporte_nestle_{f_inicio}_a_{f_fin}.csv"
            response.headers["Content-type"] = "text/csv"
            return response

        # 3. Preparar datos para la Web
        raw_datos = list(cursor)
        for item in raw_datos:
            f = str(item.get('fecha', ''))
            item['fecha_limpia'] = f[:10] if len(f) >= 10 else f
            item['json_data'] = json_util.dumps(item)

        return render_template_string(HTML_TEMPLATE, 
                                     visitas=raw_datos, 
                                     b_val=b_val, 
                                     f_inicio=f_inicio, 
                                     f_fin=f_fin)
    except Exception as e:
        return f"Error en la consulta: {e}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
