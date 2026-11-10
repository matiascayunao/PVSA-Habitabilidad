import re
from unittest.mock import patch
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from p_w_pvsa.models import Sector, Ubicacion, Piso, AsignacionLugarJefe
from p_w_pvsa.models import CategoriaObjeto, Objeto, TipoObjeto, TipoLugar, TipoLugarObjetoTipico, Lugar, ObjetoLugar, HistoricoObjeto
from p_w_pvsa.servicios.habituales import sugerencias_habituales
from p_w_pvsa.forms import ObjetoLugarFilaFormSet

class BaseHabituales(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('QA super virtual', password='qa')
        cls.mini = User.objects.create_user('QA mini virtual', password='qa')
        cls.jefe = User.objects.create_user('QA jefe virtual', password='qa')
        cls.operador = User.objects.create_user('QA operador virtual', password='qa')
        for user, name in [(cls.mini, 'Administrador'), (cls.jefe, 'Jefe de departamento'), (cls.operador, 'Operador')]:
            user.groups.add(Group.objects.get_or_create(name=name)[0])
        cls.sector = Sector.objects.create(sector='QA sector virtual')
        cls.ubicacion = Ubicacion.objects.create(ubicacion='QA ubicacion virtual', sector=cls.sector)
        cls.piso = Piso.objects.create(piso=1, ubicacion=cls.ubicacion)
        cls.tipo = TipoLugar.objects.create(tipo_de_lugar='QA tipo virtual')
        cls.lugar = Lugar.objects.create(nombre_del_lugar='QA lugar virtual', piso=cls.piso, lugar_tipo_lugar=cls.tipo)
        cls.cat = CategoriaObjeto.objects.create(nombre_de_categoria='QA categoria virtual')
        cls.obj = Objeto.objects.create(nombre_del_objeto='QA objeto virtual', objeto_categoria=cls.cat)
        cls.variante = TipoObjeto.objects.create(objeto=cls.obj, marca='QA marca', material='QA material')
        cls.variante2 = TipoObjeto.objects.create(objeto=cls.obj, marca='QA otra', material='QA material')
        cls.inv = ObjetoLugar.objects.create(lugar=cls.lugar, tipo_de_objeto=cls.variante, cantidad=10)
        AsignacionLugarJefe.objects.create(usuario=cls.jefe, lugar=cls.lugar, asignado_por=cls.admin)

    def setUp(self):
        cache.clear()
        self.client.force_login(self.admin)

    def fila(self, **extra):
        data = dict(categoria_existente=self.cat.pk, objeto_existente=self.obj.pk, tipo_objeto_existente=self.variante2.pk, cantidad=10, cantidad_mala=0, cantidad_pendiente=0, minimo_operativo=1, importancia=1)
        data.update(extra)
        return data

    def estructura(self, filas, **extra):
        data = dict(sector_existente=self.sector.pk, ubicacion_existente=self.ubicacion.pk, piso_existente=self.piso.pk, tipo_lugar_existente=self.tipo.pk, lugar_existente=self.lugar.pk, **{'obj-TOTAL_FORMS': len(filas), 'obj-INITIAL_FORMS': 0, 'obj-MIN_NUM_FORMS': 0, 'obj-MAX_NUM_FORMS': 1000})
        data.update(extra)
        for index, fila in enumerate(filas):
            for name, value in fila.items():
                data[f'obj-{index}-{name}'] = value
        return data

class VirtualesTests(BaseHabituales):

    def setUp(self):
        super().setUp()
        self.bath = TipoLugar.objects.create(tipo_de_lugar='Baño')
        self.bath_place = Lugar.objects.create(nombre_del_lugar='QA virtuales', piso=self.piso, lugar_tipo_lugar=self.bath)
        self.items = sugerencias_habituales(self.bath)

    def snap(self):
        result = {}
        with connection.cursor() as c:
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'p_w_pvsa_%' ORDER BY name")
            for name, in c.fetchall():
                c.execute('SELECT * FROM ' + connection.ops.quote_name(name))
                result[name] = {'columns': [d[0] for d in c.description], 'rows': sorted(c.fetchall(), key=repr)}
        return result

    def writes(self, queries):
        return [q['sql'] for q in queries if re.match('^\\s*(INSERT|UPDATE|DELETE|REPLACE)\\b', q['sql'], re.I)]

    def readonly(self, url, actor=None, status=200):
        before = self.snap()
        with CaptureQueriesContext(connection) as q:
            r = (actor or self.client).get(url)
        self.assertEqual(r.status_code, status)
        self.assertEqual(before, self.snap())
        self.assertEqual(self.writes(q), [])
        return r

    def row(self, index=0, **changes):
        d = dict(sugerencia_habitual=self.items[index]['referencia'], cantidad=3, cantidad_mala=0, cantidad_pendiente=0, minimo_operativo=1, importancia=2, detalle='QA virtual')
        d.update(changes)
        return d

    def data(self, rows, **extra):
        return self.estructura(rows, tipo_lugar_existente=self.bath.pk, lugar_existente=self.bath_place.pk, **extra)

    def post(self, rows):
        return self.client.post(reverse('crear_estructura'), self.data(rows))

    def invalid(self, rows):
        before = self.snap()
        with CaptureQueriesContext(connection) as q:
            r = self.post(rows)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(before, self.snap())
        self.assertEqual(self.writes(q), [])
        self.assertTrue(r.context['objetos_formset'].errors or r.context['form'].errors)
        return r

    def test_get_fallback_no_writes(self):
        r = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]))
        self.assertEqual(len(r.json()), 18)
        self.assertTrue(all((i['referencia'].startswith(f'habitual:{self.bath.pk}:') for i in r.json())))
        self.assertTrue(all((i['virtual'] and i['tipo_objeto_id'] is None for i in r.json())))

    def test_get_repeated_and_cancel(self):
        url = reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])
        first = self.readonly(url).json()
        for _ in range(3):
            self.assertEqual(self.readonly(url).json(), first)

    def test_get_configured_variants(self):
        for i, v in enumerate([self.variante, self.variante2]):
            TipoLugarObjetoTipico.objects.create(tipo_lugar=self.bath, tipo_objeto=v, orden=i)
        data = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])).json()
        self.assertEqual([i['tipo_objeto_id'] for i in data], [self.variante.pk, self.variante2.pk])
        self.assertTrue(all((set(i) == {'categoria_id', 'objeto_id', 'tipo_objeto_id', 'label'} for i in data)))

    def test_configured_json_values_unchanged(self):
        TipoLugarObjetoTipico.objects.create(tipo_lugar=self.bath, tipo_objeto=self.variante)
        item = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])).json()[0]
        self.assertEqual(item, {'categoria_id': self.cat.pk, 'objeto_id': self.obj.pk, 'tipo_objeto_id': self.variante.pk, 'label': f'{self.cat.nombre_de_categoria} - {self.obj.nombre_del_objeto}({self.variante.marca} {self.variante.material})'})

    def test_configuration_changed_after_get(self):
        TipoLugarObjetoTipico.objects.create(tipo_lugar=self.bath, tipo_objeto=self.variante)
        self.invalid([self.row()])

    def test_partial_existing_category(self):
        cat = CategoriaObjeto.objects.create(nombre_de_categoria='Infraestructura')
        data = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])).json()
        self.assertEqual(data[0]['categoria_id'], cat.pk)
        self.assertIsNone(data[0]['objeto_id'])

    def test_existing_object_other_category(self):
        obj = Objeto.objects.create(nombre_del_objeto='Paredes', objeto_categoria=self.cat)
        data = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])).json()
        self.assertEqual(data[0]['categoria_id'], self.cat.pk)
        self.assertEqual(data[0]['objeto_id'], obj.pk)
        r = self.post([self.row()])
        self.assertEqual(r.status_code, 302)
        obj.refresh_from_db()
        self.assertEqual(obj.objeto_categoria_id, self.cat.pk)

    def test_existing_blank_null_variant(self):
        obj = Objeto.objects.create(nombre_del_objeto='Paredes', objeto_categoria=self.cat)
        variant = TipoObjeto.objects.create(objeto=obj, marca=None, material='')
        r = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]))
        self.assertEqual(r.json()[0]['tipo_objeto_id'], variant.pk)
        self.assertEqual(self.post([self.row()]).status_code, 302)
        self.assertEqual(TipoObjeto.objects.filter(objeto=obj).count(), 1)

    def test_empty_kind(self):
        self.assertEqual(self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.tipo.pk])).json(), [])

    def test_invalid_kind(self):
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[999999]), status=404)

    def test_anonymous(self):
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), Client(), 302)

    def test_forbidden_role(self):
        actor = Client()
        actor.force_login(self.jefe)
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), actor, 403)

    def test_conflicting_role(self):
        self.jefe.groups.add(self.operador.groups.first())
        actor = Client()
        actor.force_login(self.jefe)
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), actor, 403)

    def test_mini_admin(self):
        actor = Client()
        actor.force_login(self.mini)
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), actor)

    def test_operator(self):
        actor = Client()
        actor.force_login(self.operador)
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), actor)

    def test_wrong_method(self):
        before = self.snap()
        r = self.client.post(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]))
        self.assertEqual(r.status_code, 405)
        self.assertEqual(before, self.snap())

    def test_csrf_absent(self):
        actor = Client(enforce_csrf_checks=True)
        actor.force_login(self.admin)
        before = self.snap()
        r = actor.post(reverse('crear_estructura'), self.data([self.row()]))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(before, self.snap())

    def test_authenticated_without_role(self):
        from django.contrib.auth.models import User
        user = User.objects.create_user('QA no role', password='qa')
        actor = Client()
        actor.force_login(user)
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk]), actor, 403)

    def test_huge_kind_id(self):
        self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[10 ** 100]), status=404)

    def test_other_ajax_gets_readonly(self):
        for name, params in [('ajax_ubicaciones_por_sector', {'sector_id': self.sector.pk}), ('ajax_pisos_por_ubicacion', {'ubicacion_id': self.ubicacion.pk}), ('ajax_lugares_por_piso', {'piso_id': self.piso.pk, 'tipo_lugar_id': self.tipo.pk}), ('ajax_objetos_por_categoria', {'categoria_id': self.cat.pk}), ('ajax_tipos_por_objeto', {'objeto_id': self.obj.pk}), ('ajax_filtros_dependientes', {})]:
            from urllib.parse import urlencode
            self.readonly(reverse(name) + ('?' + urlencode(params) if params else ''))

    def test_detail_html_escaped(self):
        value = '<img src=x onerror="alert(1)">'
        self.assertEqual(self.post([self.row(detalle=value)]).status_code, 302)
        inventory = ObjetoLugar.objects.get(lugar=self.bath_place)
        r = self.readonly(reverse('detalle_objeto_lugar', args=[inventory.pk]))
        self.assertNotContains(r, value)
        self.assertContains(r, '&lt;img')

    def test_materialize_minimum_only(self):
        before = self.snap()
        r = self.post([self.row()])
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CategoriaObjeto.objects.count(), len(before['p_w_pvsa_categoriaobjeto']['rows']) + 1)
        self.assertEqual(Objeto.objects.filter(nombre_del_objeto='Paredes').count(), 1)
        self.assertFalse(Objeto.objects.filter(nombre_del_objeto='Piso').exists())
        self.assertEqual(TipoLugarObjetoTipico.objects.count(), 0)
        self.assertEqual(ObjetoLugar.objects.filter(lugar=self.bath_place).count(), 1)
        self.assertEqual(HistoricoObjeto.objects.count(), 0)
        before_rows = {table: {row[0]: row for row in data['rows']} for table, data in before.items()}
        for table, data in self.snap().items():
            for row in data['rows']:
                if row[0] in before_rows[table]:
                    self.assertEqual(row, before_rows[table][row[0]])

    def test_multiple_virtuals(self):
        self.assertEqual(self.post([self.row(0), self.row(1)]).status_code, 302)
        self.assertEqual(ObjetoLugar.objects.filter(lugar=self.bath_place).count(), 2)
        self.assertEqual(CategoriaObjeto.objects.filter(nombre_de_categoria='Infraestructura').count(), 1)

    def test_mix_existing_virtual(self):
        normal = self.fila()
        self.assertEqual(self.post([normal, self.row()]).status_code, 302)
        self.assertEqual(ObjetoLugar.objects.filter(lugar=self.bath_place).count(), 2)

    def test_two_variants_same_object(self):
        self.assertEqual(self.post([self.fila(tipo_objeto_existente=self.variante.pk), self.fila()]).status_code, 302)

    def test_virtual_and_new_brand(self):
        manual = dict(categoria_nueva='Infraestructura', objeto_nuevo='Paredes', marca='QA distinta', material='QA otro', cantidad=2, minimo_operativo=1, importancia=1)
        self.assertEqual(self.post([self.row(), manual]).status_code, 302)
        self.assertEqual(Objeto.objects.filter(nombre_del_objeto='Paredes').count(), 1)
        self.assertEqual(TipoObjeto.objects.filter(objeto__nombre_del_objeto='Paredes').count(), 2)

    def test_new_brand_before_virtual(self):
        manual = dict(categoria_nueva='Infraestructura', objeto_nuevo='Paredes', marca='QA distinta', material='QA otro', cantidad=2, minimo_operativo=1, importancia=1)
        self.assertEqual(self.post([manual, self.row()]).status_code, 302)

    def test_invalid_among_valid(self):
        r = self.invalid([self.row(0), self.row(1, cantidad=0)])
        self.assertEqual(str(r.context['objetos_formset'].forms[1]['cantidad'].value()), '0')

    def test_bad_reference(self):
        self.invalid([self.row(sugerencia_habitual='habitual:2:forged')])

    def test_reference_other_kind(self):
        other = TipoLugar.objects.create(tipo_de_lugar='Vestidor')
        self.invalid([self.row(sugerencia_habitual=sugerencias_habituales(other)[0]['referencia'])])

    def test_reference_malformed(self):
        self.invalid([self.row(sugerencia_habitual='<script>alert(1)</script>')])

    def test_reference_too_long(self):
        self.invalid([self.row(sugerencia_habitual='x' * 121)])

    def test_category_manipulated(self):
        self.invalid([self.row(categoria_existente=self.cat.pk)])

    def test_object_manipulated(self):
        self.invalid([self.row(objeto_existente=self.obj.pk)])

    def test_variant_manipulated(self):
        self.invalid([self.row(tipo_objeto_existente=self.variante.pk)])

    def test_name_manipulated(self):
        self.invalid([self.row(objeto_nuevo='HACK')])

    def test_category_name_manipulated(self):
        self.invalid([self.row(categoria_nueva='HACK')])

    def test_brand_manipulated(self):
        self.invalid([self.row(marca='HACK')])

    def test_negative_quantity(self):
        self.invalid([self.row(cantidad=-1)])

    def test_huge_quantity(self):
        self.invalid([self.row(cantidad=10 ** 50)])

    def test_missing_quantity(self):
        self.invalid([self.row(cantidad='')])

    def test_bad_minimum(self):
        self.invalid([self.row(minimo_operativo=4)])

    def test_bad_counts(self):
        self.invalid([self.row(cantidad_mala=2, cantidad_pendiente=2)])

    def test_duplicate_virtual(self):
        self.invalid([self.row(), self.row()])

    def test_duplicate_manual_virtual(self):
        manual = dict(categoria_nueva='Infraestructura', objeto_nuevo='Paredes', cantidad=3, minimo_operativo=1)
        self.invalid([self.row(), manual])

    def test_repeated_post(self):
        self.assertEqual(self.post([self.row()]).status_code, 302)
        self.invalid([self.row()])

    def test_ref_remains_valid_after_other_save(self):
        self.assertEqual(self.post([self.row()]).status_code, 302)
        self.bath_place = Lugar.objects.create(nombre_del_lugar='QA otro destino', piso=self.piso, lugar_tipo_lugar=self.bath)
        self.assertEqual(self.post([self.row()]).status_code, 302)
        self.assertEqual(TipoObjeto.objects.filter(objeto__nombre_del_objeto='Paredes').count(), 1)

    def test_reopen_all_suggestions(self):
        refs = [i['referencia'] for i in self.items]
        self.assertEqual(self.post([self.row()]).status_code, 302)
        data = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[self.bath.pk])).json()
        self.assertEqual([i['referencia'] for i in data], refs)
        self.assertEqual(len(data), 18)

    def test_rollback_and_retry(self):
        before = self.snap()
        original = ObjetoLugar.objects.create
        calls = []

        def failing(**kw):
            calls.append(kw)
            if len(calls) == 2:
                raise ValidationError('QA forced transaction failure')
            return original(**kw)
        with patch('p_w_pvsa.servicios.estructura.ObjetoLugar.objects.create', side_effect=failing):
            r = self.post([self.row(0), self.row(1)])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(before, self.snap())
        self.assertEqual(self.post([self.row(0), self.row(1)]).status_code, 302)

    def test_all_fallback_kinds_readonly(self):
        for name in ['Vestidor', 'Comedor', 'Cafetería', 'Baño vestidor']:
            kind = TipoLugar.objects.create(tipo_de_lugar=name)
            r = self.readonly(reverse('objetos_tipicos_por_tipo_lugar', args=[kind.pk]))
            self.assertGreater(len(r.json()), 0)

    def test_formset_limit(self):
        formset = ObjetoLugarFilaFormSet({'obj-TOTAL_FORMS': '1001', 'obj-INITIAL_FORMS': '0'}, prefix='obj')
        self.assertFalse(formset.is_valid())
        self.assertEqual(len(formset.forms), 1000)
        self.assertTrue(formset.non_form_errors())

    def test_unexpected_fields_not_persisted(self):
        r = self.post([self.row(is_superuser='1', _sugerencia='forged')])
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Objeto.objects.filter(nombre_del_objeto='Paredes').count(), 1)
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.test import TransactionTestCase, Client
from django.db import connections
from django.contrib.auth.models import User
from django.urls import reverse
from p_w_pvsa.models import Sector, Ubicacion, Piso, TipoLugar, Lugar, Objeto, TipoObjeto, ObjetoLugar, CategoriaObjeto
from p_w_pvsa.servicios.habituales import sugerencias_habituales, materializar_sugerencia

class ConcurrencyTests(TransactionTestCase):

    def test_two_simultaneous_requests(self):
        user = User.objects.create_superuser('QA concurrent', password='qa')
        sector = Sector.objects.create(sector='QA concurrent')
        ubicacion = Ubicacion.objects.create(ubicacion='QA concurrent', sector=sector)
        piso = Piso.objects.create(piso=1, ubicacion=ubicacion)
        tipo = TipoLugar.objects.create(tipo_de_lugar='Baño')
        lugar = Lugar.objects.create(nombre_del_lugar='QA concurrent', piso=piso, lugar_tipo_lugar=tipo)
        ref = sugerencias_habituales(tipo)[0]['referencia']
        data = dict(sector_existente=sector.pk, ubicacion_existente=ubicacion.pk, piso_existente=piso.pk, tipo_lugar_existente=tipo.pk, lugar_existente=lugar.pk, **{'obj-TOTAL_FORMS': 1, 'obj-INITIAL_FORMS': 0, 'obj-0-sugerencia_habitual': ref, 'obj-0-cantidad': 2, 'obj-0-minimo_operativo': 1})
        actors = [Client(), Client()]
        for actor in actors:
            actor.force_login(user)
        barrier = Barrier(2)

        def delayed(item):
            barrier.wait(timeout=10)
            return materializar_sugerencia(item)

        def request(actor):
            try:
                return actor.post(reverse('crear_estructura'), data).status_code
            finally:
                connections['default'].close()
        with patch('p_w_pvsa.servicios.estructura.materializar_sugerencia', side_effect=delayed):
            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = list(pool.map(request, actors))
        self.assertTrue(all((s in (200, 302) for s in statuses)), statuses)
        if not ObjetoLugar.objects.filter(lugar=lugar).exists():
            self.assertEqual(actors[0].post(reverse('crear_estructura'), data).status_code, 302)
        self.assertEqual(ObjetoLugar.objects.filter(lugar=lugar).count(), 1)
        self.assertEqual(Objeto.objects.filter(nombre_del_objeto='Paredes').count(), 1)
        self.assertEqual(TipoObjeto.objects.filter(objeto__nombre_del_objeto='Paredes').count(), 1)
        self.assertEqual(CategoriaObjeto.objects.filter(nombre_de_categoria='Infraestructura').count(), 1)


class PhotoValidationTests(TestCase):
    def image(self, name='qa.png', format='PNG', size=(4, 4), padding=0):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        content = io.BytesIO()
        Image.new('1', size).save(content, format=format)
        return SimpleUploadedFile(name, content.getvalue() + b'0' * padding)

    def form(self, file):
        from .formularios.reporte_forms import ReportePublicoForm
        return ReportePublicoForm({'elemento_opcion': 'otro', 'otro_elemento': 'QA prueba', 'tipo_problema': 'no_funciona'}, {'foto': file})

    def test_supported_images(self):
        for name, format in [('qa.png', 'PNG'), ('qa.jpg', 'JPEG'), ('qa.jpeg', 'JPEG'), ('qa.webp', 'WEBP')]:
            with self.subTest(format=format, name=name):
                self.assertTrue(self.form(self.image(name, format)).is_valid())

    def test_supported_content_unsupported_extension(self):
        form = self.form(self.image('qa.gif'))
        self.assertFalse(form.is_valid())
        self.assertIn('foto', form.errors)

    def test_unsupported_content(self):
        self.assertFalse(self.form(self.image('qa.png', 'GIF')).is_valid())

    def test_fake_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.assertFalse(self.form(SimpleUploadedFile('qa.png', b'not an image')).is_valid())

    def test_maximum_size(self):
        self.assertFalse(self.form(self.image(padding=5 * 1024 * 1024)).is_valid())

    def test_pixel_limit(self):
        self.assertFalse(self.form(self.image(size=(5001, 4000))).is_valid())

    def test_filename_is_basename(self):
        form = self.form(self.image('../../qa.png'))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['foto'].name, 'qa.png')
