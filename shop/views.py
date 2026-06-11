from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
import threading
from django.db.models import Avg, Sum, Prefetch, Q
from .models import Product, Panier, ElementPanier, Commande, ElementCommande, Commentaire, Confiance, Categorie
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from datetime import timedelta
from django.contrib.auth import login
from .forms import InscriptionForm
from django.core.paginator import Paginator

# ─── Utilitaire panier ────────────────────────────────────────────────────────

def get_panier(request):
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
        return user_panier

    if session_panier:
        return session_panier

    panier, created = Panier.objects.get_or_create(cle_session=session_key, user=None)
    request.session['panier_id'] = panier.id
    request.session.modified = True
    return panier


# ─── Pages publiques ──────────────────────────────────────────────────────────

def home(request):
    products = Product.objects.all().order_by('-id')
    categories = Categorie.objects.all()

    recherche = request.GET.get('q')
    categorie_slug = request.GET.get('categorie')

    if recherche:
        products = products.filter(
            Q(name__icontains=recherche) |
            Q(description__icontains=recherche)
        )

    if categorie_slug:
        products = products.filter(categorie__slug=categorie_slug)

    confiance_list = Confiance.objects.all()

    # Pagination — 12 produits par page
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    return render(request, 'shop/index.html', {
        'products': products,
        'categories': categories,
        'recherche': recherche,
        'categorie_active': categorie_slug,
        'confiance_list': confiance_list,
    })

def panier(request):
    panier = get_panier(request)
    return render(request, 'shop/panier.html', {'panier': panier})


def detail_produit(request, id):
    produit = get_object_or_404(Product, id=id)  # FIX

    if request.method == "POST":
        nom = request.POST.get('nom')
        commentaire = request.POST.get('commentaire')
        note = request.POST.get('note')
        Commentaire.objects.create(
            produit=produit,
            nom=nom,
            commentaire=commentaire,
            note=note,
            actif=False
        )
        messages.success(request, "Votre avis a été soumis et sera publié après modération.")
        return redirect('detail_produit', id=id)

    commentaires = produit.commentaires.filter(actif=True)
    moyenne = commentaires.aggregate(Avg('note'))['note__avg']
    moyenne = round(moyenne, 1) if moyenne else 0

    return render(request, 'shop/detail_produit.html', {
        'produit': produit,
        'commentaires': commentaires,
        'moyenne': moyenne
    })


def a_propos(request):
    return render(request, 'shop/a_propos.html')


def contact(request):
    return render(request, 'shop/contact.html')


def confidentialites(request):
    return render(request, 'shop/confidentialite.html')


def mentions_legal(request):
    return render(request, 'shop/mentions_legal.html')


# ─── Panier ───────────────────────────────────────────────────────────────────

def ajouter_au_panier(request, product_id):
    produit = get_object_or_404(Product, id=product_id)  # FIX

    # FIX : vérification stock
    if produit.stock <= 0:
        messages.error(request, f"Désolé, « {produit.name} » est en rupture de stock.")
        return redirect('home')

    panier = get_panier(request)
    element, created = ElementPanier.objects.get_or_create(
        panier=panier,
        produit=produit
    )

    if not created:
        if element.quantite >= produit.stock:
            messages.warning(request, "Vous avez déjà le maximum disponible en stock dans votre panier.")
            return redirect('home')
        element.quantite += 1
        element.save()

    messages.success(request, f"Success ! « {produit.name} » ajouté au panier 🛒")
    return redirect('home')


def plus_quantite(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    if element.quantite < element.produit.stock:
        element.quantite += 1
        element.save()
    else:
        messages.warning(request, "Stock maximum atteint pour ce produit.")
    return redirect('panier')


def moins_quantite(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    if element.quantite > 1:
        element.quantite -= 1
        element.save()
    else:
        element.delete()
    return redirect('panier')


def supprimer_element(request, id):
    element = get_object_or_404(ElementPanier, id=id)
    element.delete()
    return redirect('panier')


# ─── Commande ─────────────────────────────────────────────────────────────────

@login_required
def page_commande(request):
    panier = get_panier(request)
    # FIX : vérifier panier non vide
    if not panier.elementpanier_set.exists():
        messages.warning(request, "Votre panier est vide.")
        return redirect('panier')
    return render(request, 'shop/commande.html')




def envoyer_mail(message):
    send_mail(
        'Nouvelle commande SenGadget',
        message,
        'sengadget.sn@gmail.com',
        ['sengadget.sn@gmail.com'],
        fail_silently=True,
    )

def envoyer_confirmation_client(email_client, nom, elements_liste, total):
        message = f"""
    Bonjour {nom} 👋,

    Merci pour votre commande sur SenGadget 🇸🇳 !

    Voici votre récapitulatif :

    """
        for e in elements_liste:
            message += f"  - {e.produit.name} x {e.quantite} = {e.produit.price * e.quantite} FCFA\n"

        message += f"""
    Total : {total} FCFA

    Notre équipe vous contactera sous peu pour confirmer la livraison.
    📞 76 252 42 96
    📍 Mbour, Sénégal

    Merci de nous faire confiance !
    — L'équipe SenGadget 🇸🇳
    """
        send_mail(
            '✅ Confirmation de votre commande SenGadget',
            message,
            'sengadget.sn@gmail.com',
            [email_client],
            fail_silently=True,
        )


@login_required
def valider_commande(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        panier = get_panier(request)
        elements = ElementPanier.objects.filter(panier=panier)
        elements_liste = list(elements)

        # FIX : vérifier panier non vide
        if not elements_liste:
            messages.error(request, "Votre panier est vide.")
            return redirect('panier')

        total = sum(e.produit.price * e.quantite for e in elements_liste)

        commande = Commande.objects.create(
            user=request.user,
            nom_complet=nom,
            telephone=telephone,
            adresse=adresse,
            montant_total=total
        )

        for e in elements_liste:
            ElementCommande.objects.create(
                commande=commande,
                produit=e.produit,
                quantite=e.quantite,
                prix=e.produit.price
            )

        elements.delete()

        message = f"""
Nouvelle commande SenGadget 🇸🇳

Nom: {nom}
Téléphone: {telephone}
Adresse: {adresse}

Produits commandés :
"""
        for e in elements_liste:
            message += f"- {e.produit.name} x {e.quantite} = {e.produit.price * e.quantite} FCFA\n"
        message += f"\nTotal: {total} FCFA"

        threading.Thread(target=envoyer_mail, args=(message,)).start()

        if request.user.email:
            threading.Thread(
                target=envoyer_confirmation_client,
                args=(request.user.email, nom, elements_liste, total)
            ).start()

        messages.success(
            request,
            "Votre commande a bien été prise en compte ✅. Vous serez contacté par notre service client dans les plus brefs délais."
        )
        return redirect('mon_compte')


# ─── Commentaires ─────────────────────────────────────────────────────────────

@login_required  # FIX
def ajouter_commentaire(request):
    if request.method == 'POST':
        produit_id = request.POST.get('produit_id')
        produit = get_object_or_404(Product, id=produit_id)  # FIX
        nom = request.POST.get('nom') or request.user.get_full_name() or request.user.username
        texte = request.POST.get('commentaire')
        note = request.POST.get('note')
        Commentaire.objects.create(
            produit=produit,
            nom=nom,
            commentaire=texte,
            note=note,
            actif=False
        )
        messages.success(request, "Votre avis a été soumis et sera publié après modération.")
    return redirect('home')


# ─── Compte client ────────────────────────────────────────────────────────────

@login_required
def mon_compte(request):
    commandes = Commande.objects.filter(user=request.user).order_by('-date_commande')
    return render(request, 'shop/mon_compte.html', {'commandes': commandes})


def signup(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('mon_compte')  # FIX : était redirect('login')
    else:
        form = InscriptionForm()
    return render(request, 'registration/signup.html', {'form': form})


# ─── Dashboard admin ──────────────────────────────────────────────────────────

@staff_member_required
def changer_statut(request, commande_id, nouveau_statut):
    STATUTS_VALIDES = {'attente', 'confirmee', 'livree', 'annulee', 'refusee'}

    # FIX : valider le statut reçu depuis l'URL
    if nouveau_statut not in STATUTS_VALIDES:
        messages.error(request, "Statut invalide.")
        return redirect('dashboard')

    commande = get_object_or_404(Commande, id=commande_id)
    commande.statut = nouveau_statut
    commande.save()

    # FIX : stock protégé contre le négatif + transaction atomique
    if nouveau_statut == 'livree':
        with transaction.atomic():
            elements = ElementCommande.objects.filter(commande=commande).select_related('produit')
            for element in elements:
                nouveau_stock = max(0, element.produit.stock - element.quantite)
                Product.objects.filter(id=element.produit.id).update(stock=nouveau_stock)

    return redirect('dashboard')


@staff_member_required
def dashboard(request):
    aujourd_hui = timezone.now().date()

    commandes = (
        Commande.objects
        .all()
        .order_by('-date_commande')
        .prefetch_related(
            Prefetch(
                'elementcommande_set',
                queryset=ElementCommande.objects.select_related('produit')
            )
        )
    )

    statut = request.GET.get('statut')
    date = request.GET.get('date')
    telephone = request.GET.get('telephone')

    if statut:
        commandes = commandes.filter(statut=statut)
    if date:
        commandes = commandes.filter(date_commande__date=date)
    if telephone:
        commandes = commandes.filter(telephone__icontains=telephone)

    total_ventes = Commande.objects.filter(statut='livree').aggregate(
        total=Sum('montant_total')
    )['total'] or 0

    nombre_commandes = commandes.count()

    ventes_du_jour = Commande.objects.filter(
        statut='livree',
        date_commande__date=aujourd_hui
    ).count()

    dates = []
    ventes_par_jour = []
    for i in range(6, -1, -1):
        jour = aujourd_hui - timezone.timedelta(days=i)
        total_jour = Commande.objects.filter(
            statut='livree',
            date_commande__date=jour
        ).aggregate(Sum('montant_total'))['montant_total__sum'] or 0
        dates.append(jour.strftime("%d/%m"))
        ventes_par_jour.append(total_jour)

    top_produits = (
        ElementCommande.objects
        .filter(commande__statut='livree')
        .values('produit__name')
        .annotate(total_vendu=Sum('quantite'))
        .order_by('-total_vendu')[:5]
    )

    maintenant = timezone.now()
    debut_mois = maintenant.replace(day=1)
    fin_mois_precedent = debut_mois - timedelta(days=1)
    debut_mois_precedent = fin_mois_precedent.replace(day=1)

    ca_mois = Commande.objects.filter(
        statut='livree',
        date_commande__gte=debut_mois
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    ca_mois_precedent = Commande.objects.filter(
        statut='livree',
        date_commande__range=(debut_mois_precedent, fin_mois_precedent)
    ).aggregate(total=Sum('montant_total'))['total'] or 0

    commandes_mois = Commande.objects.filter(
        statut='livree',
        date_commande__gte=debut_mois
    ).count()

    top_mois = (
        ElementCommande.objects
        .filter(commande__statut='livree', commande__date_commande__gte=debut_mois)
        .values('produit__name')
        .annotate(total_vendu=Sum('quantite'))
        .order_by('-total_vendu')
        .first()
    )

    evolution = 0
    if ca_mois_precedent > 0:
        evolution = ((ca_mois - ca_mois_precedent) / ca_mois_precedent) * 100

    context = {
        'commandes': commandes,
        'total_ventes': total_ventes,
        'nombre_commandes': nombre_commandes,
        'ventes_du_jour': ventes_du_jour,
        'dates': dates,
        'ventes_par_jour': ventes_par_jour,
        'top_produits': top_produits,
        'ca_mois': ca_mois,
        'commandes_mois': commandes_mois,
        'top_mois': top_mois,
        'evolution': round(evolution, 1),
    }

    return render(request, 'shop/dashboard.html', context)


@staff_member_required
def detail_commande(request, id):
    commande = get_object_or_404(Commande, id=id)
    elements = ElementCommande.objects.filter(commande=commande)
    total = sum(e.sous_total() for e in elements)
    return render(request, 'shop/detail_commande.html', {
        'commande': commande,
        'elements': elements,
        'total': total
    })