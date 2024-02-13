import requests
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
# from odoo.exceptions import UserError, AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def import_alexa(self):
        # msg_result = ""
        if self["vat"]:
            url = "https://ws2.alexiaedu.com/ACWebService/WSIntegracion.asmx/GetAlumnos"
            data = {
                'codigo': 'HbFYcML4Ti0%3d',
                'idInstitucion': '1587',
                'idCentro': '2343',
                'ejercicio': '2022',
                'check': 'B24BA-023E6-B1B93-B24A4-0863B6D1-2057',
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            response = requests.post(url, headers=headers, data=data)
            # # Puedes procesar la respuesta según tus necesidades
            if response.status_code == 200:
                # La solicitud fue exitosa
                tree = ET.ElementTree(ET.fromstring(response.text))
                root = tree.getroot()

                for datos in root.findall('datos'):
                    for alumno in datos.findall('alumno'):
                        if alumno.find('NIF').text == self["vat"]:
                            print("********************************************************************************")
                            print("Partner encontrado: " + self["name"] + " con DNI " + self["vat"])
                            print("********************************************************************************")
                            # msg_result = msg_result + "Partner encontrado: " + self["name"] + " con DNI " + self["vat"] + "\n"
                            return self

                return self.addPartner()
            else:
                print("********************************************************************************")
                print("SOLICITUD FALLIDA")
                print("********************************************************************************")
                # msg_result = msg_result + "Solicitud con Alexia fallida.\n"
                # La solicitud falló
                # Manejar el error de alguna manera
        else:
            print("********************************************************************************")
            print("Contacto desestimado: " + self["name"])
            print("¡¡Campo D.N.I. obligatorio!!")
            print("********************************************************************************")

        # raise UserError(msg_result)

    def addPartner(self):
        print("********************************************************************************")
        print("Creo el partner: " + self["name"] + " con DNI " + self["vat"])
        print("********************************************************************************")

        root = ET.Element("Alumnos")
        doc = ET.SubElement(root, "Alumno")

        Apellido1 = ET.SubElement(doc, "Apellido1", name="Apellido1")
        Apellido1.text = ""

        Apellido2 = ET.SubElement(doc, "Apellido2", name="Apellido2")
        Apellido2.text = ""

        Nombre = ET.SubElement(doc, "Nombre", name="Nombre")
        Nombre.text = self["name"]

        Pasaporte = ET.SubElement(doc, "Pasaporte", name="Pasaporte")
        Pasaporte.text = ""

        Nss = ET.SubElement(doc, "Nss", name="Nss")
        Nss.text = ""

        Sexo = ET.SubElement(doc, "Sexo", name="Sexo")
        Sexo.text = ""

        IdNacionalidadPais1 = ET.SubElement(doc, "IdNacionalidadPais1", name="IdNacionalidadPais1")
        IdNacionalidadPais1.text = ""

        Telefono1 = ET.SubElement(doc, "Telefono1", name="Telefono1")
        Telefono1.text = self["phone"]

        Telefono2 = ET.SubElement(doc, "Telefono2", name="Telefono2")
        Telefono2.text = ""

        Movil = ET.SubElement(doc, "Movil", name="Movil")
        Movil.text = self["mobile"]

        Email = ET.SubElement(doc, "Email", name="Email")
        Email.text = self["email"]

        DireccionCompleta = ET.SubElement(doc, "DireccionCompleta", name="DireccionCompleta")
        DireccionCompleta.text = self["street"]

        CodigoPostal = ET.SubElement(doc, "CodigoPostal", name="CodigoPostal")
        CodigoPostal.text = self["zip"]

        IdPais = ET.SubElement(doc, "IdPais", name="IdPais")
        IdPais.text = "724"

        Pais = ET.SubElement(doc, "Pais", name="Pais")
        Pais.text = "España"

        IdProvincia = ET.SubElement(doc, "IdProvincia", name="IdProvincia")
        IdProvincia.text = ""

        Provincia = ET.SubElement(doc, "Provincia", name="Provincia")
        Provincia.text = self["state_id"]

        Municipio = ET.SubElement(doc, "Municipio", name="Municipio")
        Municipio.text = ""

        Localidad = ET.SubElement(doc, "Localidad", name="Localidad")
        Localidad.text = self["city"]

        NacimientoFecha = ET.SubElement(doc, "NacimientoFecha", name="NacimientoFecha")
        NacimientoFecha.text = self["date_birth"]

        NacimientoFecha = ET.SubElement(doc, "NacimientoFecha", name="NacimientoFecha")
        NacimientoFecha.text = self["date_birth"]

        cXml = ET.ElementTree(root)

        data = {
            'idInstitucion': '1587',
            'idCentro': '2343',
            'codigo': 'HbFYcML4Ti0%3d',
            'xmlDatosAlta': cXml,
        }
        url = "https://ws2.alexiaedu.com/ACWebService/WSIntegracion.asmx?SetPreinscripcionDeAlumno"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, headers=headers, data=data)
        # # Puedes procesar la respuesta según tus necesidades
        if response.status_code == 200:
            print("********************************************************************************")
            print("Partner creado: " + self["name"] + " con DNI " + self["vat"])
            print("********************************************************************************")
        else:
            print("********************************************************************************")
            print("Partner no creado: " + self["name"] + " con DNI " + self["vat"])
            print("********************************************************************************")


