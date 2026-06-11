from django.contrib import admin
from .models import Product, Panier, ElementPanier, Commande, ElementCommande, Commentaire, Confiance, Categorie
from django.utils.text import slugify


# permettre a admiin d'ajouter ces produits
admin.site.register(Product)
admin.site.register(Panier)
admin.site.register(ElementPanier)
admin.site.register(Commande)
admin.site.register(ElementCommande)
admin.site.register(Commentaire)
admin.site.register(Confiance)
admin.site.register(Categorie)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    search_fields = ('nom',)

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.nom)
        super().save_model(request, obj, form, change)