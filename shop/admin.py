from django.contrib import admin
from .models import Product, Panier, ElementPanier, Commande, ElementCommande, Commentaire, Confiance, Categorie


# permettre a admiin d'ajouter ces produits
admin.site.register(Product)
admin.site.register(Panier)
admin.site.register(ElementPanier)
admin.site.register(Commande)
admin.site.register(ElementCommande)
admin.site.register(Commentaire)
admin.site.register(Confiance)
admin.site.register(Categorie)

