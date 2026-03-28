from django import forms
from .models import Buyurtma
import re


class BuyurtmaForm(forms.ModelForm):

    class Meta:
        model = Buyurtma
        fields = ['tel_raqam', 'manzil']

        widgets = {
            'tel_raqam': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': '+998 90 123 45 67'
                }
            ),
            'manzil': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Yetkazib berish manzilini kiriting...'
                }
            ),
        }

        labels = {
            'tel_raqam': "Telefon raqam",
            'manzil': "Yetkazib berish manzili",
        }

    def clean_tel_raqam(self):
        tel = self.cleaned_data.get('tel_raqam')

        pattern = r"^\+998\d{9}$"

        tel = tel.replace(" ", "")

        if not re.match(pattern, tel):
            raise forms.ValidationError(
                "Telefon raqam +998901234567 formatida bo‘lishi kerak."
            )

        return tel

    def clean_manzil(self):
        manzil = self.cleaned_data.get('manzil')

        if len(manzil) < 10:
            raise forms.ValidationError(
                "Manzil juda qisqa. To‘liq manzil kiriting."
            )

        return manzil