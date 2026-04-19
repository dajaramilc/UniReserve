# UniReserve - Sistema de Gestión de Reservas Universitarias

UniReserve es una plataforma digital para la gestión de reservas de espacios y servicios universitarios.  
El sistema centraliza la administración de recursos académicos y deportivos, permitiendo registrar usuarios, consultar recursos, crear reservas, validar disponibilidad y gestionar cancelaciones.

Este proyecto corresponde a:

- **Taller 1 / Entrega 1:** Núcleo de negocio y exposición de API profesional (Django REST Framework).
- **Taller 2 / Entrega 2:** Migración a microservicios con el **patrón Strangler Fig** (Django + Flask + Nginx + Docker).

---

# Taller 2 — Migración a Microservicios

## Arquitectura resultante

```
                    ┌───────────────────────┐
     Cliente ─────► │   Nginx (puerto 80)   │
                    └──────────┬────────────┘
                               │
             ┌─────────────────┼──────────────────────┐
             │ /api/, /admin/  │  /api/v2/payments/   │
             ▼                                        ▼
   ┌────────────────────┐                  ┌──────────────────────┐
   │ django_web :8000   │  HTTP  POST      │ flask_microservice   │
   │ Django + DRF       │ ───────────────► │      :5000           │
   │ (resources,        │                  │ (procesamiento pago) │
   │  reservations,     │                  └──────────────────────┘
   │  admin)            │
   └────────────────────┘
```

- **Nginx** enruta `/api/v2/payments/*` → `flask_microservice`; el resto →
  `django_web`.
- **Django** sigue siendo el núcleo del dominio y, cuando un recurso es
  premium, llama al microservicio Flask vía HTTP desde
  `CreateReservationService._process_payment` (URL configurable con la
  variable de entorno `PAYMENTS_SERVICE_URL`).
- **Flask** responde `200 success=true` (gateway `fake`) o `402 success=false`
  (gateway `rejected`).

## Cómo levantar todo (Docker)

```bash
docker compose up --build
```

Puntos de entrada:

| URL                                            | Destino                       |
|------------------------------------------------|-------------------------------|
| `http://localhost/`                            | Django vía Nginx              |
| `http://localhost/admin/`                      | Admin Django                  |
| `http://localhost/api/resources/`              | API DRF                       |
| `http://localhost/api/reservations/`           | API DRF                       |
| `http://localhost/api/v2/payments/process`     | Microservicio Flask           |
| `http://localhost:8000`                        | Django directo (bypass Nginx) |
| `http://localhost:5000`                        | Flask directo (bypass Nginx)  |

## Setup mínimo de datos

```bash
docker compose exec django_web python manage.py createsuperuser
```
Luego en `http://localhost/admin/`:
1. Crear al menos 1 `User` (`role=student`, `account_status=active`).
2. Crear al menos 1 `Resource` con `is_premium=True` e `is_active=True`
   (cobro fijo de 25 000, ver `ReservationPricingService`).

Probar el microservicio aislado:
```bash
curl -X POST http://localhost/api/v2/payments/process \
     -H "Content-Type: application/json" \
     -d '{"user_id":1,"user_email":"a@b.c","amount":25000,"resource_id":1,"payment_provider":"fake"}'
```

---

# Entrega 1 — Núcleo de Negocio y API Profesional

---

# Objetivo de la entrega

Desarrollar el **backend del sistema UniReserve** aplicando buenas prácticas de arquitectura de software y diseño de APIs.

El sistema implementa:

- API REST con **Django REST Framework**
- **Service Layer** para desacoplar lógica de negocio
- **Patrones de diseño creacionales**
- Validación de reglas de negocio
- Manejo adecuado de códigos HTTP
- Arquitectura modular y extensible

---

# Dominio del sistema

El dominio original del sistema define **7 entidades principales**:

- Usuario
- Recurso
- Reserva
- Horario
- Pago
- InventarioRecurso
- Cancelación

Para esta entrega se implementó el **57.1 % del dominio (4 de 7 entidades)**:

- `User`
- `Resource`
- `Schedule`
- `Reservation`

Esto cumple con el requisito del entregable de implementar entre **50 % y 60 % del dominio**.

---

# Tecnologías utilizadas

- Python 3.11
- Django
- Django REST Framework
- SQLite
- Git + GitHub

---


---

# Arquitectura del sistema

El sistema sigue una arquitectura por capas con separación clara de responsabilidades.

Cliente
│
▼
APIView (views.py)
│
▼
Serializers
│
▼
Service Layer (services.py)
│
▼
Domain Components (builders, factories)
│
▼
Models (models.py)
│
▼
Base de datos


---


---

# Capas de la aplicación

## Models

Representan las entidades persistentes del dominio:

- User
- Resource
- Schedule
- Reservation

---

## Services

Contiene la lógica de negocio y los casos de uso del sistema.

Ejemplos:

- CreateReservationService
- CancelReservationService
- ListUserReservationHistoryService
- ReservationPricingService

Toda la lógica del sistema se ejecuta aquí.

---

## Serializers

Validan y transforman los datos de entrada y salida de la API.

Ejemplos:

- UserSerializer
- ResourceSerializer
- ReservationSerializer
- CreateReservationInputSerializer

---

## Views

Exponen los endpoints usando **APIView** de Django REST Framework.

Las views no contienen lógica de negocio, solo:

- reciben requests
- validan datos
- llaman servicios
- devuelven respuestas HTTP

---

## Domain

Contiene componentes auxiliares del dominio.

### Builders

Implementa el patrón **Builder**.

Se usa `ReservationBuilder` para construir reservas de forma controlada.

---

### Factories

Implementa el patrón **Factory**.

`PaymentGatewayFactory` permite seleccionar diferentes pasarelas de pago.

---

### Exceptions

Centraliza las excepciones de dominio.

Ejemplos:

- UserNotFoundError
- ResourceUnavailableError
- PaymentFailedError
- ReservationAlreadyCancelledError

---

# Patrones de diseño utilizados

## Builder

Se utiliza `ReservationBuilder` para construir la entidad `Reservation`.

Esto permite crear reservas paso a paso y validar los atributos antes de persistirlos.

Beneficios:

- Construcción clara de objetos complejos
- Menor acoplamiento
- Código más legible

---

## Factory

Se utiliza `PaymentGatewayFactory` para abstraer la creación de pasarelas de pago.

Esto permite cambiar fácilmente entre distintos proveedores de pago.

Implementaciones actuales:

- FakePaymentGateway
- RejectedPaymentGateway

---

# Endpoints disponibles

## Listar recursos

GET /api/resources/


Devuelve todos los recursos disponibles en el sistema.

---

## Crear reserva


POST /api/reservations/


Ejemplo de request:

```json
{
  "user_id": 1,
  "resource_id": 1,
  "date": "2026-03-10",
  "start_time": "10:00:00",
  "end_time": "11:00:00"
}

Respuesta esperada:

HTTP 201 Created
Cancelar reserva
DELETE /api/reservations/{reservation_id}/cancel/

Ejemplo:

DELETE /api/reservations/1/cancel/
Historial de reservas de un usuario
GET /api/users/{user_id}/reservations/

Ejemplo:

GET /api/users/1/reservations/


Reglas de negocio implementadas

Un usuario debe estar activo para reservar.

El horario debe ser válido (start_time < end_time).

Un recurso inactivo no puede reservarse.

No pueden existir traslapes de horario para un mismo recurso.

Si el recurso es premium se procesa pago.

Una reserva cancelada no puede cancelarse nuevamente.

Códigos HTTP utilizados
Código	Significado
201	Reserva creada correctamente
400	Datos inválidos
404	Recurso o usuario inexistente
409	Conflicto de horario o reserva cancelada
