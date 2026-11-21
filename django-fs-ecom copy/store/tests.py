from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Product


class StorePageTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Trail Mug',
            description='A durable everyday mug.',
            price='24.50',
            stock=2,
        )

    def test_product_detail_uses_the_product_template(self):
        self.client.force_login(
            User.objects.create_user(username='shopper', password='test-password')
        )
        response = self.client.get(
            reverse('product_detail', args=[self.product.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Trail Mug')
        self.assertContains(response, 'Add to cart')
        self.assertNotContains(response, 'Product Form')

    def test_custom_not_found_page_is_rendered(self):
        with override_settings(DEBUG=False):
            response = self.client.get('/this-page-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "We couldn't find that page", status_code=404)


class StoreActionTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Trail Mug',
            description='A durable everyday mug.',
            price='24.50',
            stock=1,
        )
        self.customer = User.objects.create_user(
            username='customer',
            password='test-password',
        )

    def test_add_to_cart_adds_item_and_respects_stock(self):
        self.client.force_login(self.customer)
        url = reverse('add_to_cart', args=[self.product.id])

        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['cart'], {str(self.product.id): 1})

        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['cart'], {str(self.product.id): 1})
        self.assertContains(response, 'out of stock')

    def test_staff_can_add_update_and_delete_products(self):
        staff = User.objects.create_user(
            username='staff',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(staff)

        response = self.client.get(reverse('add_product'))
        self.assertContains(response, 'Add a product')

        response = self.client.post(reverse('add_product'), {
            'name': 'Desk Lamp',
            'description': 'Warm reading light.',
            'price': '39.99',
            'stock': 3,
            'image': '',
        })
        self.assertRedirects(response, reverse('home'))
        new_product = Product.objects.get(name='Desk Lamp')

        response = self.client.post(
            reverse('update_product', args=[new_product.id]),
            {
                'name': 'Desk Lamp Pro',
                'description': 'Updated reading light.',
                'price': '44.99',
                'stock': 4,
                'image': '',
            },
        )
        self.assertRedirects(response, reverse('home'))
        new_product.refresh_from_db()
        self.assertEqual(new_product.name, 'Desk Lamp Pro')

        response = self.client.get(
            reverse('delete_product', args=[new_product.id])
        )
        self.assertContains(response, 'Yes, delete product')
        response = self.client.post(
            reverse('delete_product', args=[new_product.id])
        )
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(Product.objects.filter(pk=new_product.id).exists())

    def test_navigation_logs_out_with_post(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse('home'))
        self.assertContains(response, 'action="{}"'.format(reverse('logout')))

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
