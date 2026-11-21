
from django import forms
from .models import Product


# PRODUCT FORM
class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            'name',
            'description',
            'price',
            'stock',
            'image'
        ]


# CHECKOUT FORM
class CheckoutForm(forms.Form):

    address = forms.CharField(
        widget=forms.Textarea,
        min_length=10
    )
