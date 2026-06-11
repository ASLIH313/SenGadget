from django.test import TestCase, Client
from django.contrib.auth.models import User
from shop.models import Product, Categorie, Panier, ElementPanier, Commande


class TestPanier(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@gmail.com',
            password='testpass123'
        )
        self.categorie = Categorie.objects.create(
            nom='Audio',
            slug='audio'
        )
        self.produit = Product.objects.create(
            name='Écouteurs Test',
            price=5000,
            description='Test description',
            stock=10,
            categorie=self.categorie
        )
        self.produit_hors_stock = Product.objects.create(
            name='Produit épuisé',
            price=3000,
            description='Rupture',
            stock=0
        )


    # ─── Panier ───────────────────────────────────────────────────────────────

    def test_ajouter_produit_au_panier(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/ajouter/{self.produit.id}/')
        self.assertEqual(response.status_code, 302)
        panier = Panier.objects.get(user=self.user)
        self.assertEqual(panier.elementpanier_set.count(), 1)

    def test_produit_hors_stock_bloque(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.get(f'/ajouter/{self.produit_hors_stock.id}/')
        panier = Panier.objects.filter(user=self.user).first()
        if panier:
            self.assertEqual(panier.elementpanier_set.count(), 0)

    def test_produit_inexistant_renvoie_404(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/ajouter/99999/')
        self.assertEqual(response.status_code, 404)


    # ─── Commande ─────────────────────────────────────────────────────────────

    def test_valider_commande(self):
        self.client.login(username='testuser', password='testpass123')
        self.client.get(f'/ajouter/{self.produit.id}/')
        response = self.client.post('/commande/valider/', {
            'nom': 'Aslih Test',
            'telephone': '771234567',
            'adresse': 'Dakar Test'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Commande.objects.filter(user=self.user).count(), 1)

    def test_commande_panier_vide_redirige(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/commande/valider/', {
            'nom': 'Aslih Test',
            'telephone': '771234567',
            'adresse': 'Dakar Test'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Commande.objects.filter(user=self.user).count(), 0)

    def test_commande_sans_connexion_redirige_login(self):
        response = self.client.post('/commande/valider/', {
            'nom': 'Anonyme',
            'telephone': '770000000',
            'adresse': 'Quelque part'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


    # ─── Recherche ────────────────────────────────────────────────────────────

    def test_recherche_produit_existant(self):
        response = self.client.get('/?q=Écouteurs')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Écouteurs Test')

    def test_recherche_produit_inexistant(self):
        response = self.client.get('/?q=xyzinexistant')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aucun produit')

    def test_filtre_categorie(self):
        response = self.client.get('/?categorie=audio')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Écouteurs Test')


    # ─── Accès dashboard ──────────────────────────────────────────────────────

    def test_dashboard_interdit_visiteur(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_interdit_client_normal(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_staff(self):
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)


    # ─── Pages publiques ──────────────────────────────────────────────────────

    def test_page_accueil(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_detail_produit(self):
        response = self.client.get(f'/produit/{self.produit.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Écouteurs Test')

    def test_detail_produit_inexistant(self):
        response = self.client.get('/produit/99999/')
        self.assertEqual(response.status_code, 404)