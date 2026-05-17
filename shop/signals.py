from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Panier, ElementPanier

@receiver(user_logged_in)
def merge_panier_on_login(sender, user, request, **kwargs):
    """
    Fusionne le panier anonyme (stocké par id dans request.session['panier_id'])
    dans le panier de l'utilisateur lors de la connexion.
    """
    panier_id = request.session.get('panier_id')
    if not panier_id:
        return

    try:
        session_panier = Panier.objects.get(id=panier_id, user__isnull=True)
    except Panier.DoesNotExist:
        return

    user_panier, _ = Panier.objects.get_or_create(user=user)

    for el in session_panier.elementpanier_set.all():
        up_el, created = ElementPanier.objects.get_or_create(
            panier=user_panier,
            produit=el.produit,
            defaults={'quantite': el.quantite}
        )
        if not created:
            up_el.quantite += el.quantite
            up_el.save()

    session_panier.delete()
    request.session.pop('panier_id', None)
    request.session.modified = True