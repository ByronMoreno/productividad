import os
import json
import re
from openai import OpenAI

class AIService:
    @staticmethod
    def mock_classify_text(text: str) -> dict:
        """
        Simulador local de IA (Mock AI) basado en reglas para cuando falla la cuota de la API
        o no hay conexión de internet.
        """
        text_lower = text.lower()
        
        # Valores por defecto
        title = text[:100].strip()
        description = f"Procesado en modo local (sin cuota de IA). Texto original: {text}"
        project_name = "General"
        energy = 3
        priority = "MEDIUM"
        estimated_time = 30
        due_date = None

        # Detección de proyectos y atributos mediante palabras clave
        if any(w in text_lower for w in ["tesis", "clase", "moodle", "docencia", "alumno", "universidad", "exponer"]):
            project_name = "Docencia"
            energy = 4
            priority = "HIGH"
            estimated_time = 90
        elif any(w in text_lower for w in ["docker", "python", "devops", "deploy", "server", "aws", "git", "java", "api", "base de datos", "código"]):
            project_name = "DevOps/Desarrollo"
            energy = 5
            priority = "HIGH"
            estimated_time = 120
        elif any(w in text_lower for w in ["bolsa", "inversión", "invertir", "acciones", "dinero", "broker", "mercado"]):
            project_name = "Bolsa"
            energy = 3
            priority = "MEDIUM"
            estimated_time = 45
        elif any(w in text_lower for w in ["médico", "salud", "ejercicio", "correr", "gimnasio", "entrenar", "dieta", "comida"]):
            project_name = "Salud"
            energy = 2
            priority = "MEDIUM"
            estimated_time = 60
        elif any(w in text_lower for w in ["comprar", "arroz", "supermercado", "limpiar", "ordenar", "lavar", "carro"]):
            project_name = "Vida Personal"
            energy = 1
            priority = "LOW"
            estimated_time = 30

        # Detección simple de fechas límites
        if "hoy" in text_lower:
            from datetime import date
            due_date = date.today().isoformat()
        elif "mañana" in text_lower:
            from datetime import date, timedelta
            due_date = (date.today() + timedelta(days=1)).isoformat()
        elif "viernes" in text_lower:
            from datetime import date, timedelta
            today = date.today()
            # Buscar el próximo viernes
            days_ahead = 4 - today.weekday()
            if days_ahead <= 0: # ya pasó o es viernes
                days_ahead += 7
            due_date = (today + timedelta(days=days_ahead)).isoformat()

        return {
            "title": title,
            "description": description,
            "project_name": project_name,
            "energy": energy,
            "priority": priority,
            "estimated_time": estimated_time,
            "due_date": due_date
        }

    @staticmethod
    def classify_text(text: str) -> dict:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return AIService.mock_classify_text(text)
            
        client = OpenAI(api_key=api_key)
        
        system_prompt = (
            "Eres el motor de inteligencia artificial de TaskFlow OS, un sistema zen de productividad.\n"

            "Tu tarea es analizar el pensamiento o idea que el usuario ha capturado en su bandeja de entrada (Inbox) "
            "y clasificarlo estructurando una tarea en formato JSON.\n\n"
            "Debes responder ÚNICAMENTE con un objeto JSON que siga exactamente este esquema:\n"
            "{\n"
            "  \"title\": \"Título resumido, accionable y claro (en español)\",\n"
            "  \"description\": \"Detalles adicionales o notas (en español, puede ser vacío o null)\",\n"
            "  \"project_name\": \"Nombre del proyecto o área al que pertenece (ej: Docencia, DevOps/Desarrollo, Bolsa, Salud, Vida Personal, etc.)\",\n"
            "  \"energy\": 3,\n"
            "  \"priority\": \"MEDIUM\",\n"
            "  \"estimated_time\": 30,\n"
            "  \"due_date\": \"YYYY-MM-DD\" or null\n"
            "}\n"
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Clasifica este pensamiento: {text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result_content = response.choices[0].message.content
            return json.loads(result_content)
        except Exception as e:
            # Si hay cuota excedida (429) o cualquier error, caemos en el Mock local
            print(f"Llamando a OpenAI API falló ({e}). Usando clasificador local de respaldo.")
            return AIService.mock_classify_text(text)

    @staticmethod
    def get_coach_response(user_message: str, energy_limit: int, pending_tasks: list) -> str:
        api_key = os.environ.get('OPENAI_API_KEY')
        
        # Obtener contexto del Segundo Cerebro
        from app.knowledge.models import KnowledgeNode
        knowledge_nodes = KnowledgeNode.query.all()
        
        # Función local de coach zen de respaldo
        def local_coach_response():
            energy_desc = {1: "Baja 🔋", 2: "Media ⚡", 3: "Alta 🚀"}[energy_limit]
            task_count = len(pending_tasks)
            max_energy = {1: 2, 2: 4, 3: 5}[energy_limit]
            suitable_tasks = [t for t in pending_tasks if t.energy <= max_energy]
            
            response = f"[Modo Zen Local] Hola. Tu energía de hoy está configurada como {energy_desc}.\n"
            if task_count == 0:
                response += "No tienes tareas pendientes ahora mismo. Es un excelente momento para descansar."
            else:
                response += f"Tienes {task_count} tareas en tu lista global. "
                if len(suitable_tasks) > 0:
                    first_task = suitable_tasks[0]
                    response += f"Te sugiero enfocarte hoy en: '{first_task.title}' "
                    response += f"(requiere energía: {first_task.energy}/5). "
                else:
                    response += "Ninguna de tus tareas se adecúa a tu nivel de energía bajo de hoy. Te sugiero descansar."
            
            # Mencionar notas si la consulta es técnica y hay coincidencias
            msg_lower = user_message.lower()
            matching_notes = [n for n in knowledge_nodes if n.title.lower() in msg_lower or any(w in msg_lower for w in n.title.lower().split())]
            if matching_notes:
                response += f"\n\n[Segundo Cerebro] He encontrado estas notas técnicas en tu base de conocimientos que te podrían ayudar:\n"
                for note in matching_notes:
                    response += f"- '{note.title}' (puedes consultarla en la sección Segundo Cerebro)."
            return response

        if not api_key:
            return local_coach_response()

        client = OpenAI(api_key=api_key)
        energy_desc = {1: "Baja 🔋", 2: "Media ⚡", 3: "Alta 🚀"}[energy_limit]
        
        tasks_summary = []
        for t in pending_tasks:
            tasks_summary.append(f"- {t.title} [Estimado: {t.estimated_time}m, Energía Requerida: {t.energy}/5, Proyecto: {t.project.name if t.project else 'Ninguno'}]")
        tasks_str = "\n".join(tasks_summary) if tasks_summary else "No hay tareas pendientes en este momento."

        knowledge_summary = [f"- {n.title}" for n in knowledge_nodes]
        knowledge_str = "\n".join(knowledge_summary) if knowledge_summary else "No hay notas registradas."

        system_prompt = (
            "Eres el IA Coach de TaskFlow OS. Tu objetivo es ayudar al usuario a gestionar su energía mental, "
            "reducir el estrés, y avanzar en sus tareas de forma estructurada y con mínima fatiga visual y mental.\n"

            "Sé empático, calmado y muy conciso. No respondas con largas listas de consejos. Recomienda una acción clara.\n\n"
            "CONTEXTO ACTUAL DEL USUARIO:\n"
            f"- Límite de energía para hoy: {energy_desc}\n"
            f"- Tareas pendientes:\n{tasks_str}\n\n"
            "NOTAS DEL SEGUNDO CEREBRO (BASE DE CONOCIMIENTO):\n"
            f"{knowledge_str}\n\n"
            "Instrucciones:\n"
            "- Si el usuario te consulta sobre cómo hacer algo, busca si en las NOTAS DEL SEGUNDO CEREBRO hay una que coincida. "
            "De ser así, menciónale el nombre exacto de la nota y sugiérele consultarla.\n"
            "- Si está abrumado, recomiéndale descansar.\n"
            "- Mantén las respuestas en un tono zen y de pocas palabras."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error en IA Coach API: {e}. Usando Coach Zen Local.")
            return local_coach_response()

    @staticmethod
    def mock_agent_debate(energy_limit: int, pending_tasks: list) -> tuple:
        """
        Simulador local de debate multi-agente en caso de error de API o cuota de OpenAI.
        """
        energy_desc = {1: "Baja 🔋", 2: "Media ⚡", 3: "Alta 🚀"}[energy_limit]
        max_energy = {1: 2, 2: 4, 3: 5}[energy_limit]
        
        # Agrupar tareas por proyectos
        docencia_tasks = [t for t in pending_tasks if t.project and t.project.name.lower() in ["docencia", "universidad"]]
        devops_tasks = [t for t in pending_tasks if t.project and any(w in t.project.name.lower() for w in ["devops", "desarrollo", "programación", "code"])]
        bolsa_tasks = [t for t in pending_tasks if t.project and t.project.name.lower() in ["bolsa", "inversión"]]
        salud_tasks = [t for t in pending_tasks if t.project and t.project.name.lower() in ["salud", "personal", "vida"]]
        general_tasks = [t for t in pending_tasks if not t.project or t.project.name not in ["Docencia", "Bolsa", "Salud", "DevOps/Desarrollo"]]

        dialogues = []
        dialogues.append("🧘 <strong>Coach Zen:</strong> Bienvenidos, agentes. El usuario tiene la energía en nivel: <b>" + energy_desc + "</b>. Debatamos qué tarea priorizar hoy.")

        # Intervención de Docencia
        if docencia_tasks:
            dialogues.append(f"🎓 <strong>Agente Docencia:</strong> Defiendo mis prioridades. Tenemos la tarea '{docencia_tasks[0].title}' pendiente. Es vital para las clases y alumnos.")
        else:
            dialogues.append("🎓 <strong>Agente Docencia:</strong> No tengo tareas críticas hoy, me mantengo al margen.")

        # Intervención de DevOps
        if devops_tasks:
            dialogues.append(f"💻 <strong>Agente DevOps/Código:</strong> El desarrollo y la infraestructura no esperan. Propongo avanzar con '{devops_tasks[0].title}' (Energía: {devops_tasks[0].energy}/5).")
        else:
            dialogues.append("💻 <strong>Agente DevOps/Código:</strong> El repositorio está estable por ahora.")

        # Intervención de Bolsa
        if bolsa_tasks:
            dialogues.append(f"📈 <strong>Agente Inversiones:</strong> Sugiero revisar '{bolsa_tasks[0].title}'. El mercado se mueve rápido y requiere nuestra atención.")
        else:
            dialogues.append("📈 <strong>Agente Inversiones:</strong> Las inversiones están tranquilas el día de hoy.")

        # Intervención de Salud/Vida
        if salud_tasks:
            dialogues.append(f"🔋 <strong>Agente Salud/Personal:</strong> ¡Un momento! La salud es lo primero. Si la energía es {energy_desc}, sugiero priorizar '{salud_tasks[0].title}' y no sobrecargar el cerebro.")
        else:
            dialogues.append("🔋 <strong>Agente Salud/Personal:</strong> Recomiendo reservar espacios de descanso e hidratación entre bloques.")

        # Resolución del Coach Zen
        suitable_tasks = [t for t in pending_tasks if t.energy <= max_energy]
        recommendations = []
        if suitable_tasks:
            selected = suitable_tasks[0]
            dialogues.append(f"🧘 <strong>Coach Zen (Resolución):</strong> Colegas, habiendo analizado el balance y la energía {energy_desc}, he decidido que la tarea óptima para hoy será: <b>'{selected.title}'</b>. Agente de Salud, vigila las pausas.")
            recommendations.append(selected.title)
            # Agregar otra opcional si hay
            if len(suitable_tasks) > 1:
                recommendations.append(suitable_tasks[1].title)
        else:
            dialogues.append("🧘 <strong>Coach Zen (Resolución):</strong> No hay tareas que se ajusten a la energía baja de hoy. La resolución del comité es declarar el día como de <b>Descanso Cognitivo y Replanificación</b>.")
            recommendations.append("Descanso y Reorganización de pendientes")

        transcript = "<br><br>".join(dialogues)
        return transcript, recommendations

    @staticmethod
    def simulate_agent_debate(energy_limit: int, pending_tasks: list) -> tuple:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return AIService.mock_agent_debate(energy_limit, pending_tasks)

        client = OpenAI(api_key=api_key)
        energy_desc = {1: "Baja 🔋", 2: "Media ⚡", 3: "Alta 🚀"}[energy_limit]
        
        tasks_summary = []
        for t in pending_tasks:
            tasks_summary.append(f"- {t.title} [Energía Requerida: {t.energy}/5, Proyecto: {t.project.name if t.project else 'Ninguno'}]")
        tasks_str = "\n".join(tasks_summary) if tasks_summary else "No hay tareas pendientes."

        system_prompt = (
            "Eres el moderador de un debate multi-agente en TaskFlow OS.\n"

            "Debes simular un diálogo de consenso en español entre 4 agentes especializados:\n"
            "1) Agente Docencia (🎓): Defiende temas de clases, alumnos y tesis.\n"
            "2) Agente DevOps/Código (💻): Defiende programación, servidores e infraestructuras.\n"
            "3) Agente Inversiones (📈): Defiende análisis de bolsa y mercados.\n"
            "4) Agente Salud/Personal (🔋): Defiende descanso, ejercicio y vida familiar.\n"
            "5) Coach Zen (🧘) (Moderador): Toma la decisión final.\n\n"
            "CONTEXTO DEL USUARIO:\n"
            f"- Energía del usuario hoy: {energy_desc}\n"
            f"- Tareas pendientes:\n{tasks_str}\n\n"
            "Instrucciones:\n"
            "- Escribe una transcripción fluida, corta y entretenida en español donde los agentes expongan sus posturas de forma lógica basándose en las tareas cargadas.\n"
            "- Cada agente debe tener 1 o 2 intervenciones.\n"
            "- Al final, el Coach Zen debe decidir las 2 tareas recomendadas para hoy basándose estrictamente en el límite de energía.\n"
            "- Formatea la salida como un objeto JSON estructurado con estas dos llaves:\n"
            "{\n"
            "  \"transcript\": \"Diálogo completo formateado con HTML (tags strong, br, etc.) para verse estético.\",\n"
            "  \"recommendations\": [\"Tarea 1 sugerida\", \"Tarea 2 sugerida\"]\n"
            "}"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Genera el debate del comité de agentes para la organización de hoy."}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            data = json.loads(response.choices[0].message.content)
            return data.get('transcript', ''), data.get('recommendations', [])
        except Exception as e:
            print(f"Error simulando debate multi-agente con OpenAI API: {e}. Usando Mock local.")
            return AIService.mock_agent_debate(energy_limit, pending_tasks)

    @staticmethod
    def mock_generate_time_blocking(energy_limit: int, pending_tasks: list, selected_date) -> list:
        """
        Generador local de Time Blocking basado en reglas.
        Detecta horas fijas (ej: 'a las 18:00') en el título/descripción y agenda el resto flexiblemente.
        """
        from datetime import time, timedelta, datetime
        import re
        
        def extract_time(title, desc):
            full_text = f"{title or ''} {desc or ''}".lower()
            m1 = re.search(r'\b(\d{1,2}):(\d{2})\b', full_text)
            if m1:
                h, m = int(m1.group(1)), int(m1.group(2))
                if 0 <= h < 24 and 0 <= m < 60:
                    return time(h, m)
            m2 = re.search(r'\ba\s+las\s+(\d{1,2})\b|\b(\d{1,2})\s*h(oras)?\b', full_text)
            if m2:
                val = m2.group(1) or m2.group(2)
                h = int(val)
                if 0 <= h < 24:
                    return time(h, 0)
            return None

        # Filtrar tareas aptas según energía si no están en progreso
        max_energy = {1: 2, 2: 4, 3: 5}[energy_limit]
        tasks_to_schedule = [t for t in pending_tasks if t.energy <= max_energy or t.status == 'PROGRESS']
        if not tasks_to_schedule and pending_tasks:
            tasks_to_schedule = [pending_tasks[0]]

        blocks = []
        fixed_blocks = []
        flexible_tasks = []

        # Paso A: Procesar primero tareas con hora fija
        for task in tasks_to_schedule:
            t_fixed = extract_time(task.title, task.description)
            if t_fixed:
                duration = max(task.estimated_time or 30, 30)
                start_dt = datetime.combine(selected_date, t_fixed)
                end_dt = start_dt + timedelta(minutes=duration)
                fixed_blocks.append({
                    "title": task.title,
                    "task_id": task.id,
                    "start_dt": start_dt,
                    "end_dt": end_dt
                })
            else:
                flexible_tasks.append(task)

        # Añadir las fijas a la lista final de bloques
        for fb in fixed_blocks:
            blocks.append({
                "title": fb["title"],
                "task_id": fb["task_id"],
                "start_time": fb["start_dt"].time().strftime('%H:%M'),
                "end_time": fb["end_dt"].time().strftime('%H:%M')
            })

        # Paso B: Distribuir tareas flexibles a partir de las 09:00 AM cuidando superposiciones
        current_dt = datetime.combine(selected_date, time(9, 0))
        
        for task in flexible_tasks:
            duration = max(task.estimated_time or 30, 30)
            
            # Buscar un hueco donde la tarea no choque con las fijas
            while True:
                potential_end = current_dt + timedelta(minutes=duration)
                
                # Verificar si choca con algún bloque fijo
                collision = False
                for fb in fixed_blocks:
                     # Si se superponen los rangos
                     if not (potential_end <= fb["start_dt"] or current_dt >= fb["end_dt"]):
                         collision = True
                         # Mover la hora de inicio al final de la tarea fija que causó la colisión
                         current_dt = fb["end_dt"] + timedelta(minutes=15)
                         break
                
                if not collision:
                    break
            
            blocks.append({
                "title": task.title,
                "task_id": task.id,
                "start_time": current_dt.time().strftime('%H:%M'),
                "end_time": potential_end.time().strftime('%H:%M')
            })
            
            current_dt = potential_end + timedelta(minutes=15)

        # Ordenar todos los bloques cronológicamente
        blocks.sort(key=lambda x: x["start_time"])

        if not blocks:
            blocks.append({
                "title": "Planificación y Lectura Ligera",
                "task_id": None,
                "start_time": "09:00",
                "end_time": "10:00"
            })
            blocks.append({
                "title": "Descanso y Meditación Zen",
                "task_id": None,
                "start_time": "10:15",
                "end_time": "11:00"
            })

        return blocks


    @staticmethod
    def generate_time_blocking(energy_limit: int, pending_tasks: list, selected_date, daily_objective: str = None) -> list:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return AIService.mock_generate_time_blocking(energy_limit, pending_tasks, selected_date)
            
        client = OpenAI(api_key=api_key)
        energy_desc = {1: "Baja 🔋", 2: "Media ⚡", 3: "Alta 🚀"}[energy_limit]
        
        tasks_summary = []
        for t in pending_tasks:
            tasks_summary.append(f"- ID: {t.id} | {t.title} [Estimado: {t.estimated_time}m, Energía: {t.energy}/5]")
        tasks_str = "\n".join(tasks_summary) if tasks_summary else "No hay tareas pendientes."
        
        objective_prompt = ""
        if daily_objective:
            objective_prompt = f"- OBJETIVO PRIORITARIO DE HOY: '{daily_objective}'\n(Por favor, planifica bloques de alta energía o los primeros bloques del día específicamente para avanzar en este objetivo).\n"

        system_prompt = (
            "Eres el planificador de tiempo zen de TaskFlow OS.\n\n"
            "Tu objetivo es crear el itinerario de Time Blocking para el día de hoy.\n"
            "Debes organizar las tareas del usuario en bloques lógicos, empezando a las 09:00 AM.\n"
            "Instrucciones:\n"
            "- Respeta el límite de energía actual del usuario. No agendes tareas pesadas si su energía es Baja.\n"
            "- Intercala descansos zen de 10 a 15 minutos entre tareas.\n"
            "- Si una tarea ya está en proceso (PROGRESS), agéndala primero.\n"
            f"{objective_prompt}"
            "- Responde con un objeto JSON que contenga la llave \"blocks\" con el array de bloques:\n"
            "{\n"
            "  \"blocks\": [\n"
            "    {\n"
            "      \"title\": \"Nombre de la actividad o descanso\",\n"
            "      \"task_id\": 123 (o null si es un bloque libre/descanso),\n"
            "      \"start_time\": \"09:00\",\n"
            "      \"end_time\": \"10:15\"\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
        
        try:
            user_content = f"Organiza mi día. Energía: {energy_desc}."
            if daily_objective:
                user_content += f" Mi objetivo de hoy es: '{daily_objective}'."
            user_content += f" Tareas disponibles:\n{tasks_str}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            result_content = response.choices[0].message.content
            data = json.loads(result_content)
            return data.get("blocks", AIService.mock_generate_time_blocking(energy_limit, pending_tasks, selected_date))
        except Exception as e:
            print(f"Error generando Time Blocking con OpenAI API: {e}. Usando generador local.")
            return AIService.mock_generate_time_blocking(energy_limit, pending_tasks, selected_date)



