from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.exceptions import ValidationError


class UserRole(models.TextChoices):
    CEO             = 'CEO',             'CEO'
    INTERNAL        = 'INTERNAL',        'Interno'
    CLIENT_MARLUVAS = 'CLIENT_MARLUVAS', 'Cliente Marluvas'
    CLIENT_TECMATER = 'CLIENT_TECMATER', 'Cliente Tecmater'
    ANONYMOUS       = 'ANONYMOUS',       'An\u00f3nimo'


class Permission(models.TextChoices):
    ASK_KNOWLEDGE_OPS      = 'ask_knowledge_ops',      'Ask Knowledge Ops'
    ASK_KNOWLEDGE_PRODUCTS = 'ask_knowledge_products', 'Ask Knowledge Products'
    ASK_KNOWLEDGE_PRICING  = 'ask_knowledge_pricing',  'Ask Knowledge Pricing'
    VIEW_EXPEDIENTES_OWN   = 'view_expedientes_own',   'View Expedientes Own'
    VIEW_EXPEDIENTES_ALL   = 'view_expedientes_all',   'View Expedientes All'
    VIEW_COSTOS            = 'view_costos',             'View Costos'
    DOWNLOAD_DOCUMENTS     = 'download_documents',     'Download Documents'
    MANAGE_USERS           = 'manage_users',            'Manage Users'


ROLE_PERMISSION_CEILING = {
    UserRole.CEO: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.ASK_KNOWLEDGE_PRICING, Permission.VIEW_EXPEDIENTES_OWN,
        Permission.VIEW_EXPEDIENTES_ALL, Permission.VIEW_COSTOS,
        Permission.DOWNLOAD_DOCUMENTS, Permission.MANAGE_USERS,
    ],
    UserRole.INTERNAL: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_ALL, Permission.VIEW_COSTOS,
        Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.CLIENT_MARLUVAS: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_OWN, Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.CLIENT_TECMATER: [
        Permission.ASK_KNOWLEDGE_OPS, Permission.ASK_KNOWLEDGE_PRODUCTS,
        Permission.VIEW_EXPEDIENTES_OWN, Permission.DOWNLOAD_DOCUMENTS,
    ],
    UserRole.ANONYMOUS: [],
}


class MWTUser(AbstractUser):
    role            = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CEO)
    objects         = UserManager()
    legal_entity    = models.ForeignKey(
        'core.LegalEntity',
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    whatsapp_number = models.CharField(max_length=20, null=True, blank=True)
    is_api_user     = models.BooleanField(default=False)
    is_blocked      = models.BooleanField(default=False)
    brand           = models.ForeignKey(
        'brands.Brand',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_users',
    )
    created_by      = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='created_users',
    )

    class Meta:
        verbose_name = 'Usuario MWT'
        verbose_name_plural = 'Usuarios MWT'

    def has_permission(self, perm) -> bool:
        ceiling = ROLE_PERMISSION_CEILING.get(self.role, [])
        if perm not in ceiling:
            return False
        return self.permissions_set.filter(permission=perm).exists()

    def __str__(self):
        return f'{self.username} ({self.role})'


class UserPermission(models.Model):
    user       = models.ForeignKey(MWTUser, on_delete=models.CASCADE, related_name='permissions_set')
    permission = models.CharField(max_length=50, choices=Permission.choices)
    granted_by = models.ForeignKey(
        MWTUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions',
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'permission')
        verbose_name = 'Permiso de Usuario'
        verbose_name_plural = 'Permisos de Usuarios'

    def save(self, *args, **kwargs):
        ceiling = ROLE_PERMISSION_CEILING.get(self.user.role, [])
        if self.permission not in ceiling:
            raise ValidationError(
                f"El permiso '{self.permission}' est\u00e1 fuera del techo del rol '{self.user.role}'."
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} \u2192 {self.permission}'
