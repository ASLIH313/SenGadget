from django.db.models import Sum


def panier_context(request):
    from shop.models import Panier, ElementPanier

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    panier_id = request.session.get('panier_id')
    session_panier = None
    if panier_id:
        try:
            session_panier = Panier.objects.get(id=panier_id, user__isnull=True)
        except Panier.DoesNotExist:
            session_panier = None

    if request.user.is_authenticated:
        user_panier, _ = Panier.objects.get_or_create(user=request.user)
        if session_panier:
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
        panier = user_panier
    elif session_panier:
        panier = session_panier
    else:
        panier, created = Panier.objects.get_or_create(cle_session=session_key, user=None)
        request.session['panier_id'] = panier.id
        request.session.modified = True

    panier_count = panier.elementpanier_set.aggregate(
        total=Sum('quantite')
    )['total'] or 0

    return {
        'panier': panier,
        'panier_non_vide': panier_count > 0,
        'panier_count': panier_count,
    }