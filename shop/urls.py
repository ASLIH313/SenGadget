from django.urls import path
from .views import home
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .forms import EmailAuthenticationForm  

urlpatterns = [
    path('', home, name='home'),
    path('panier/', views.panier, name='panier'),
    path('ajouter/<int:product_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    
    path('panier/plus/<int:id>/', views.plus_quantite, name='plus_quantite'),
    path('panier/moins/<int:id>/', views.moins_quantite, name='moins_quantite'),
    path('panier/supprimer/<int:id>/', views.supprimer_element, name='supprimer_element'),

    path('commande/', views.page_commande, name='page_commande'),
    path('commande/valider/', views.valider_commande, name='valider_commande'),

    path('commentaire/', views.ajouter_commentaire, name='ajouter_commentaire'),

    path('produit/<int:id>/', views.detail_produit, name='detail_produit'),

    path('a-propos/', views.a_propos, name='a_propos'),

    path('contact/', views.contact, name='contact'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('changer-statut/<int:commande_id>/<str:nouveau_statut>/', views.changer_statut, name='changer_statut'),

    path('dashboard/commande/<int:id>/', views.detail_commande, name='detail_commande'),

    path('confidentialites/', views.confidentialites, name='confidentialites'),

    path('mentions_legal/', views.mentions_legal, name='mentions_legal'),

    path('mon-compte/', views.mon_compte, name='mon_compte'),

    path('signup/', views.signup, name='signup'),

    path('accounts/login/', LoginView.as_view(authentication_form=EmailAuthenticationForm, template_name='registration/login.html'), name='login'),
]

