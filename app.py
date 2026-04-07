import os
import json
import pandas as pd  # Necesitarás: pip install pandas openpyxl
from flask import Flask, render_template_string, request, make_response
from pymongo import MongoClient
from bson import json_util
from io import BytesIO

app = Flask(__name__)

# --- CONEXIÓN A MONGO ---
MONGO_URI = "mongodb+srv://ANDRES_VANEGAS:CF32fUhOhrj70dY5@cluster0.dtureen.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['NestleDB']
visitas_col = db['visitas']

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NestleDB - Filtros Avanzados</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; font-family: 'Segoe UI', sans-serif; }
        .main-container { padding: 20px; max-width: 1200px; margin: auto; }
        .filter-panel { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 5px solid #0056b3; }
        .table-card { background: white; border-radius: 15px; margin-top: 20px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .empty-state { padding: 50px; text-align: center; color: #6c757d; }
        .btn-detail { background: none; border: none; color: #0d6efd; text-decoration: underline; font-weight: bold; padding: 0; }
        iframe { width: 100%; height: 400px; border-radius: 10px; border: 0; }
        .img-full { width: 100%; border-radius: 8px; border: 1px solid #ddd; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="text-center mb-4">
            <h2 class="fw-bold text-dark">🔍 Consulta de Visitas Nestle</h2>
            <p class="text-muted">Selecciona un rango de fechas para iniciar la búsqueda</p>
        </div>

        <div class="filter-panel">
            <form method="GET" class="row g-3">
                <div class="col-md-4">
                    <label class="form-label fw-bold small">Búsqueda por texto (Opcional)</label>
                    <input type="text" name="busqueda" class="form-control" placeholder="PV, BMB, Usuario..." value="{{ b_val }}">
                </div>
                <div class="col-md-3">
                    <label class="form-label fw-bold small">Fecha Inicial</label>
                    <input type="date" name="fecha_inicio" class="form-control" value="{{ f_inicio }}" required>
                </div>
                <div class="col-md-3">
                    <label class="form-label fw-bold small">Fecha Final</label>
                    <input type="date" name="fecha_fin" class="form-control" value="{{ f_fin }}" required>
                </div>
                <div class="col-md-2 d-flex align-items-end gap-2">
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Consultar</button>
                </div>
                
                {% if visitas %}
                <div class="col-12 mt-3 d-flex justify-content-between align-items-center">
                    <span class="badge bg-info text-dark">Resultados encontrados: {{ visitas|length }}</span>
                    <div class="btn-group">
                        <button type="submit" name="descargar" value="excel" class="btn btn-success">📊 Descargar Excel</button>
                        <a href="/" class="btn btn-outline-secondary">Limpiar</a>
                    </div>
                </div>
                {% endif %}
            </form>
        </div>

        <div class="table-card">
            {% if not visitas and not buscado %}
                <div class="empty-state">
                    <h4>👋 Bienvenido</h4>
                    <p>Usa los filtros de arriba para cargar la información del día.</p>
                </div>
            {% elif not visitas and buscado %}
                <div class="empty-state">
                    <h4>No se encontraron datos</h4>
                    <p>Intenta con un rango de fechas diferente.</p>
                </div>
            {% else %}
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Fecha Hora</th>
                                <th>PV / BMB</th>
                                <th>Usuario</th>
                                <th>GPS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for v in visitas %}
                            <tr>
                                <td class="small">{{ v.fecha }}</td>
                                <td>
                                    <button class="btn-detail" onclick='verDetalles({{ v.json_data | safe }})'>
                                        {{ v.pv }} <br>
                                        <small class="text-muted">BMB: {{ v.bmb }}</small>
                                    </button>
                                </td>
                                <td>{{ v.usuario }}</td>
                                <td>
                                    {% if v.gps %}
                                        <button class="btn btn-sm btn-outline-danger rounded-pill" onclick="verMapa('{{ v.gps }}')">📍 Mapa</button>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% endif %}
        </div>
    </div>

    <div class="modal fade" id="detallesModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header bg-dark text-white"><h6>Detalles de la Visita</h6><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div>
                <div class="modal-body">
                    <div id="contenidoDetalles"></div>
                    <div class="row mt-3">
                        <div class="col-6"><p class="small fw-bold">Foto BMB:</p><div id="fotoBMB"></div></div>
                        <div class="col-6"><p class="small fw-bold">Foto Fachada:</p><div id="fotoFachada"></div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="mapModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-lg">
            <div class="modal-content">
                <div class="modal-body p-0"><iframe id="mapFrame" src=""></iframe></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const mDetalles = new bootstrap.Modal(document.getElementById('detallesModal'));
        const mMapa = new bootstrap.Modal(document.getElementById('mapModal'));

        function verDetalles(data) {
            let html = "";
            for (let key in data) {
                if (!key.startsWith('f_') && !['_id', 'json_data', 'fecha_limpia'].includes(key)) {
                    html += `<div class="py-1 border-bottom small"><b class="text-primary">${key}:</b> ${data[key] || '---'}</div>`;
                }
            }
            document.getElementById('contenidoDetalles').innerHTML = html;
            document.getElementById('fotoBMB').innerHTML = data.f_bmb ? `<img src="${data.f_bmb}" class="img-full">` : 'N/A';
            document.getElementById('fotoFachada').innerHTML = data.f_fachada ? `<img src="${data.f_fachada}" class="img-full">` : 'N/A';
            mDetalles.show();
        }

        function verMapa(coords) {
            document.getElementById('mapFrame').src = `https://maps.google.com/maps?q=${coords}&z=16&output=embed`;
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

    query = {}
    buscado = False

    # Solo ejecutamos la consulta si hay fechas seleccionadas
    if f_inicio and f_fin:
        buscado = True
        
        # Ajuste de rango para contemplar las 24 horas del día final
        # MongoDB compara strings, así que "2026-03-12" incluye hasta el inicio de ese día.
        # Al poner "2026-03-12 23:59:59" nos aseguramos de traer todo.
        query["fecha"] = {
            "$gte": f"{f_inicio} 00:00:00",
            "$lte": f"{f_fin} 23:59:59"
        }

        if b_val:
            query["$or"] = [
                {"pv": {"$regex": b_val, "$options": "i"}},
                {"bmb": {"$regex": b_val, "$options": "i"}},
                {"usuario": {"$regex": b_val, "$options": "i"}}
            ]

        cursor = visitas_col.find(query).sort("fecha", -1)

        # Lógica de descarga en Excel
        if descargar == "excel":
            df = pd.DataFrame(list(cursor))
            if not df.empty:
                # Limpiar columnas no deseadas para el reporte
                columnas_a_quitar = [c for c in df.columns if c.startswith('f_') or c == '_id']
                df = df.drop(columns=columnas_a_quitar)
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Visitas')
                
                output.seek(0)
                response = make_response(output.getvalue())
                response.headers["Content-Disposition"] = f"attachment; filename=Reporte_Nestle_{f_inicio}.xlsx"
                response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                return response
            return "No hay datos para exportar"

        # Carga normal para la web
        datos = list(cursor)
        for item in datos:
            item['json_data'] = json_util.dumps(item)
            
        return render_template_string(HTML_TEMPLATE, visitas=datos, b_val=b_val, f_inicio=f_inicio, f_fin=f_fin, buscado=buscado)

    # Si no hay filtros, mostramos la página vacía (Empty State)
    return render_template_string(HTML_TEMPLATE, visitas=[], b_val="", f_inicio="", f_fin="", buscado=False)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
