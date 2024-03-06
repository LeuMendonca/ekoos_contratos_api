from ninja import NinjaAPI
from contratos.api import router as router_contratos

api = NinjaAPI()

api.add_router('/' , router_contratos)