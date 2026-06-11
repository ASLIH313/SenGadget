from django.db import models
from django.contrib.auth.models import User


#le model categorie pour classer les produits en fonction de leur type
class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

#le model produit stocke les infos de chaque produit et la categorie a laquelle il appartient
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    # NOUVEAU
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produits'
    )

    def __str__(self):
        return self.name
    




#le model panier appartient a un visiteur meme sil na pas de compte 
class Panier(models.Model):
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='panier'
    )
    cle_session = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def total_panier(self):
        elements = self.elementpanier_set.all()
        return sum([e.sous_total() for e in elements])

    def __str__(self):
        if self.user:
            return f"Panier utilisateur {self.user.email or self.user.username}"
        return f"Panier session {self.cle_session}"



#le model les elements d'un panier klkjonque un panier peut contenir plusieurs produits. stocke produit et quantite
class ElementPanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('panier', 'produit')

    def sous_total(self):
        return self.produit.price * self.quantite

    def __str__(self):
        return f"{self.produit.name} x {self.quantite}"



#le model commande quand le client confirme, stocke les infos client 
class Commande(models.Model):

    STATUT_CHOICES = [
        ('attente', 'En attente de confirmation'),
        ('confirmee', 'Confirmée par téléphone'),
        ('livree', 'Livrée au client'),
        ('annulee', 'Annulée'),
        ('refusee', 'Refusée à la livraison'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nom_complet = models.CharField(max_length=200)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    montant_total = models.IntegerField()

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='attente'
    )

    date_commande = models.DateTimeField(auto_now_add=True)
    
    def total_reel(self):
        return sum(e.sous_total() for e in self.elementcommande_set.all())

    def __str__(self):
        return f"Commande de {self.nom_complet}- {self.statut}"
    



#le model element commande stocke produit et quantite d'une commande 
class ElementCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix = models.PositiveIntegerField()

    def sous_total(self):
        return self.prix * self.quantite

    def __str__(self):
        return f"{self.produit.name} x {self.quantite}"


#le model commentaires pour les avis et produits 
class Commentaire(models.Model):
    produit = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='commentaires')
    nom = models.CharField(max_length=100)
    commentaire = models.TextField()
    note = models.IntegerField(default=5)
    date = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=False)

    def __str__(self):
        return self.nom

#le model confiance pour ajouter les points necessaire pour la section nous faire confiance
class Confiance(models.Model):
    icone = models.CharField(max_length=50)  # ex: 'fa-shipping-fast'
    titre = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.titre