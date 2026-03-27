# Sprint 18 - URL patterns para views_sprint18.py
from django.urls import path
from . import views_sprint18 as v

urlpatterns = [
    # T1.2 PATCH por estado
    path('<uuid:pk>/confirmado/', v.patch_confirmado, name='exp-patch-confirmado'),
    path('<uuid:pk>/preparacion/', v.patch_preparacion, name='exp-patch-preparacion'),
    path('<uuid:pk>/produccion/', v.patch_produccion, name='exp-patch-produccion'),
    path('<uuid:pk>/despacho/', v.patch_despacho, name='exp-patch-despacho'),
    path('<uuid:pk>/transito/', v.patch_transito, name='exp-patch-transito'),
    # T1.3 FactoryOrder CRUD
    path('<uuid:pk>/factory-orders/', v.factory_orders_list, name='exp-factory-orders-list'),
    path('<uuid:pk>/factory-orders/<int:fo_id>/', v.factory_orders_detail, name='exp-factory-orders-detail'),
    # T1.4 Pagos
    path('<uuid:pk>/pagos/', v.pagos_list, name='exp-pagos-list'),
    path('<uuid:pk>/pagos/<int:pago_id>/confirmar/', v.pago_confirmar, name='exp-pago-confirmar'),
    # T1.5 Merge
    path('<uuid:pk>/merge/', v.merge_expedientes, name='exp-merge'),
    # T1.6 Split
    path('<uuid:pk>/separate-products/', v.split_expediente, name='exp-split'),
]
