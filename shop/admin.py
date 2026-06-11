from django.contrib import admin
from .models import Product, Panier, ElementPanier, Commande, ElementCommande, Commentaire, Confiance, Categorie
from django.utils.text import slugify


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    search_fields = ('nom',)

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.nom)
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'categorie')
    list_filter = ('categorie',)
    search_fields = ('name',)
    list_editable = ('price', 'stock')


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'telephone', 'montant_total', 'statut', 'date_commande')
    list_filter = ('statut', 'date_commande')
    search_fields = ('nom_complet', 'telephone')
    ordering = ('-date_commande',)


@admin.register(ElementCommande)
class ElementCommandeAdmin(admin.ModelAdmin):
    list_display = ('commande', 'produit', 'quantite', 'prix')


@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ('nom', 'produit', 'note', 'actif', 'date')
    list_filter = ('actif', 'note')
    list_editable = ('actif',)
    search_fields = ('nom', 'commentaire')


@admin.register(Confiance)
class ConfianceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'icone')


admin.site.register(Panier)
admin.site.register(ElementPanier)