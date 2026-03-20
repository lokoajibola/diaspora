from decimal import Decimal
from xml.sax.saxutils import escape

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product


CATEGORY_DATA = [
    {
        'name': 'Food',
        'slug': 'food',
        'items': {
            'NG': [
                ('Poundo Yam Flour 2.2kg', Decimal('27000.00')),
                ('Bournvita Jar 500g', Decimal('6900.00')),
                ('Pure Coconut Water Pack', Decimal('5000.00')),
                ('Ginger Wellness Drink', Decimal('1300.00')),
                ('Shelled Pumpkin Seeds', Decimal('7500.00')),
            ],
            'GH': [
                ('Banku Mix Flour', Decimal('14000.00')),
                ('Sobolo Concentrate', Decimal('6500.00')),
                ('Kelewele Spice Blend', Decimal('3800.00')),
                ('Roasted Groundnut Combo', Decimal('5500.00')),
                ('Cassava Flour Family Pack', Decimal('9800.00')),
            ],
        },
    },
    {
        'name': 'Shoes',
        'slug': 'shoes',
        'items': {
            'NG': [
                ('White Airforce Sneakers', Decimal('35000.00')),
                ('Quality Vans Sneakers', Decimal('35000.00')),
                ('Running Shoes', Decimal('22000.00')),
                ('Luxury Hugo Slides', Decimal('56000.00')),
                ('Ladies Sneakers', Decimal('20000.00')),
            ],
            'GH': [
                ('Accra Street Sneakers', Decimal('32000.00')),
                ('Classic Leather Loafers', Decimal('28000.00')),
                ('Weekend Slide Sandals', Decimal('18000.00')),
                ('Office Derby Shoes', Decimal('41000.00')),
                ('Sport Runner Trainers', Decimal('26000.00')),
            ],
        },
    },
    {
        'name': 'Men Fashion',
        'slug': 'men-fashion',
        'items': {
            'NG': [
                ('Senator Kaftan Set', Decimal('28000.00')),
                ('Adire Casual Shirt', Decimal('14500.00')),
                ('Premium Agbada Outfit', Decimal('65000.00')),
                ('Slim Fit Native Trousers', Decimal('18500.00')),
                ('Leather Wristwatch', Decimal('27000.00')),
            ],
            'GH': [
                ('Kente Trim Shirt', Decimal('22000.00')),
                ('Classic Smock Top', Decimal('29000.00')),
                ('Tailored Chino Set', Decimal('24000.00')),
                ('Weekend Linen Set', Decimal('21000.00')),
                ('Gold Accent Wristwatch', Decimal('32000.00')),
            ],
        },
    },
    {
        'name': 'Women Fashion',
        'slug': 'women-fashion',
        'items': {
            'NG': [
                ('Ankara Maxi Dress', Decimal('24000.00')),
                ('Boubou Lounge Dress', Decimal('30000.00')),
                ('Office Blouse and Skirt Set', Decimal('26000.00')),
                ('Elegant Headwrap Bundle', Decimal('12000.00')),
                ('Beaded Occasion Gown', Decimal('54000.00')),
            ],
            'GH': [
                ('Kente Midi Dress', Decimal('27000.00')),
                ('Accra Brunch Jumpsuit', Decimal('25000.00')),
                ('Printed Wrap Dress', Decimal('23000.00')),
                ('Sheer Sleeve Blouse', Decimal('16000.00')),
                ('Festival Occasion Gown', Decimal('50000.00')),
            ],
        },
    },
    {
        'name': 'Beauty',
        'slug': 'beauty',
        'items': {
            'NG': [
                ('Raw Shea Butter Tub', Decimal('8500.00')),
                ('Glow Face Serum', Decimal('12000.00')),
                ('Braided Wig Unit', Decimal('48000.00')),
                ('Complete Makeup Kit', Decimal('36000.00')),
                ('Black Soap Care Set', Decimal('9500.00')),
            ],
            'GH': [
                ('Whipped Shea Butter Jar', Decimal('9000.00')),
                ('Cocoa Glow Body Oil', Decimal('11000.00')),
                ('Lace Front Wig Unit', Decimal('52000.00')),
                ('Daily Beauty Essentials', Decimal('28000.00')),
                ('Natural Hair Moisture Set', Decimal('14500.00')),
            ],
        },
    },
    {
        'name': 'Accessories',
        'slug': 'accessories',
        'items': {
            'NG': [
                ('Leather Handbag', Decimal('26000.00')),
                ('Travel School Backpack', Decimal('18000.00')),
                ('Beaded Necklace Set', Decimal('9500.00')),
                ('Mini Crossbody Bag', Decimal('14000.00')),
                ('Weekend Tote Bag', Decimal('22000.00')),
            ],
            'GH': [
                ('Kente Detail Handbag', Decimal('28000.00')),
                ('Structured Work Tote', Decimal('24000.00')),
                ('Festival Bead Set', Decimal('12500.00')),
                ('Everyday Sling Bag', Decimal('15000.00')),
                ('Carry-On Travel Backpack', Decimal('21000.00')),
            ],
        },
    },
]


VENDOR_DATA = {
    'NG': [
        ('2348001000001', 'Amina', 'Balogun'),
        ('2348001000002', 'Chinedu', 'Okoro'),
        ('2348001000003', 'Efe', 'Ighalo'),
        ('2348001000004', 'Kemi', 'Adewale'),
        ('2348001000005', 'Tunde', 'Bello'),
    ],
    'GH': [
        ('2332401000001', 'Ama', 'Mensah'),
        ('2332401000002', 'Kojo', 'Owusu'),
        ('2332401000003', 'Yaa', 'Boateng'),
        ('2332401000004', 'Kwaku', 'Asare'),
        ('2332401000005', 'Abena', 'Adjei'),
    ],
}


COUNTRY_LABELS = {
    'NG': 'Nigeria',
    'GH': 'Ghana',
}


class Command(BaseCommand):
    help = 'Seeds the marketplace with demo vendors and products using safe local placeholder images.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        vendors = self._create_vendors(user_model)
        categories = self._create_categories()
        products_created = self._create_products(vendors, categories)

        self.stdout.write(self.style.SUCCESS('Seed completed successfully.'))
        self.stdout.write(self.style.SUCCESS(f'Vendors available: {sum(len(items) for items in VENDOR_DATA.values())}'))
        self.stdout.write(self.style.SUCCESS(f'Products created or updated: {products_created}'))
        self.stdout.write(self.style.WARNING('Vendor password for seeded accounts: VendorPass123!'))

    def _create_vendors(self, user_model):
        vendors = {'NG': [], 'GH': []}
        for country_code, entries in VENDOR_DATA.items():
            for phone_number, first_name, last_name in entries:
                user, _ = user_model.objects.get_or_create(phone_number=phone_number)
                user.first_name = first_name
                user.last_name = last_name
                user.role = 'vendor'
                user.country = country_code
                user.is_active = True
                user.set_password('VendorPass123!')
                user.save()
                vendors[country_code].append(user)
        return vendors

    def _create_categories(self):
        categories = {}
        for entry in CATEGORY_DATA:
            category, _ = Category.objects.get_or_create(
                slug=entry['slug'],
                defaults={'name': entry['name']},
            )
            if category.name != entry['name']:
                category.name = entry['name']
                category.save(update_fields=['name'])
            categories[entry['slug']] = category
        return categories

    def _create_products(self, vendors, categories):
        total = 0
        for category_entry in CATEGORY_DATA:
            category = categories[category_entry['slug']]
            for country_code, items in category_entry['items'].items():
                country_vendors = vendors[country_code]
                for index, (name, price) in enumerate(items):
                    vendor = country_vendors[index % len(country_vendors)]
                    product_name = f'{name} ({COUNTRY_LABELS[country_code]})'
                    product, _ = Product.objects.get_or_create(
                        vendor=vendor,
                        name=product_name,
                        defaults={
                            'category': category,
                            'country': country_code,
                            'description': self._build_description(name, category.name, country_code, vendor.first_name),
                            'base_price': price,
                            'markup_percentage': Decimal('12.50'),
                            'stock': 5 + index,
                            'is_active': True,
                        },
                    )
                    product.category = category
                    product.country = country_code
                    product.description = self._build_description(name, category.name, country_code, vendor.first_name)
                    product.base_price = price
                    product.markup_percentage = Decimal('12.50')
                    product.stock = 5 + index
                    product.is_active = True
                    image_name = f'{slugify(country_code)}-{slugify(category.slug)}-{slugify(name)}.svg'
                    product.image.save(
                        image_name,
                        ContentFile(self._build_svg(product_name, category.name, country_code)),
                        save=False,
                    )
                    product.save()
                    total += 1
        return total

    def _build_description(self, name, category_name, country_code, vendor_name):
        country_label = COUNTRY_LABELS[country_code]
        return (
            f'{name} sourced for diaspora shoppers from {country_label}. '
            f'Listed under {category_name} by {vendor_name} with export-friendly packaging and international dispatch support.'
        )

    def _build_svg(self, name, category_name, country_code):
        title = escape(name)
        category = escape(category_name)
        country = escape(COUNTRY_LABELS[country_code])
        palette = {
            'NG': ('#0b6b4b', '#d7f4e7', '#0f172a'),
            'GH': ('#9f1239', '#fde68a', '#111827'),
        }
        primary, secondary, text_color = palette[country_code]
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
<rect width="800" height="800" rx="48" fill="{secondary}"/>
<rect x="48" y="48" width="704" height="220" rx="36" fill="{primary}" opacity="0.95"/>
<circle cx="650" cy="620" r="110" fill="{primary}" opacity="0.12"/>
<circle cx="180" cy="660" r="72" fill="{primary}" opacity="0.10"/>
<text x="80" y="140" fill="#ffffff" font-size="34" font-family="Arial, Helvetica, sans-serif">Diaspora Way</text>
<text x="80" y="205" fill="#ffffff" font-size="54" font-weight="700" font-family="Arial, Helvetica, sans-serif">{title}</text>
<text x="80" y="370" fill="{text_color}" font-size="30" font-family="Arial, Helvetica, sans-serif">Category</text>
<text x="80" y="418" fill="{text_color}" font-size="44" font-weight="700" font-family="Arial, Helvetica, sans-serif">{category}</text>
<text x="80" y="520" fill="{text_color}" font-size="30" font-family="Arial, Helvetica, sans-serif">Country</text>
<text x="80" y="568" fill="{text_color}" font-size="44" font-weight="700" font-family="Arial, Helvetica, sans-serif">{country}</text>
<text x="80" y="690" fill="{primary}" font-size="28" font-family="Arial, Helvetica, sans-serif">Demo catalog image generated locally</text>
</svg>'''.encode('utf-8')
