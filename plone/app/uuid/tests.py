# -*- coding: utf-8 -*-
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.uuid.testing import PLONE_APP_UUID_FUNCTIONAL_TESTING
from plone.app.uuid.testing import PLONE_APP_UUID_INTEGRATION_TESTING

import time
import unittest


class IntegrationTestCase(unittest.TestCase):
    layer = PLONE_APP_UUID_INTEGRATION_TESTING

    def test_assignment(self):
        from plone.uuid.interfaces import IUUID

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')

        d1 = portal['d1']
        uuid = IUUID(d1)

        self.assertTrue(isinstance(uuid, str))

    def test_search(self):
        from plone.uuid.interfaces import IUUID

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')
        portal.invokeFactory('Document', 'd2')

        d1 = portal['d1']
        uuid = IUUID(d1)

        catalog = portal['portal_catalog']
        results = catalog(UID=uuid)

        self.assertEqual(1, len(results))
        self.assertEqual(uuid, results[0].UID)
        self.assertEqual('/'.join(d1.getPhysicalPath()), results[0].getPath())

    def test_uuidToPhysicalPath(self):
        from plone.uuid.interfaces import IUUID
        from plone.app.uuid.utils import uuidToPhysicalPath

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')
        portal.invokeFactory('Document', 'd2')

        d1 = portal['d1']
        uuid = IUUID(d1)

        self.assertEqual('/'.join(d1.getPhysicalPath()),
                         uuidToPhysicalPath(uuid))

    def test_speed(self):
        # I updated some of the utility functions to be a bit faster.
        # In this function you can check the speed.
        from Acquisition import aq_base
        from plone.uuid.interfaces import IUUID
        from plone.app.uuid.utils import uuidToPhysicalPath
        from plone.app.uuid.utils import uuidToURL
        from plone.app.uuid.utils import uuidToObject

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        start = time.time()
        uuids = {}
        total = 40
        for i in range(total):
            doc_id = portal.invokeFactory('Document', 'd{}'.format(i))
            doc = portal[doc_id]
            uuids[IUUID(doc)] = {
                'path': '/'.join(doc.getPhysicalPath()),
                'url': doc.absolute_url(),
                'obj': aq_base(doc),
            }
        end = time.time()
        print("Time taken to create {} items: {}".format(total, end - start))

        self.assertEqual(len(uuids), total)
        start = time.time()
        for uuid, info in uuids.items():
            self.assertEqual(info['path'], uuidToPhysicalPath(uuid))
        end = time.time()
        print("Time taken for uuidToPhysicalPath: {}".format(end - start))

        start = time.time()
        for uuid, info in uuids.items():
            self.assertEqual(info['url'], uuidToURL(uuid))
        end = time.time()
        print("Time taken for uuidToURL: {}".format(end - start))

        start = time.time()
        for uuid, info in uuids.items():
            self.assertEqual(info['obj'], aq_base(uuidToObject(uuid)))
        end = time.time()
        print("Time taken for uuidToObject: {}".format(end - start))

    def test_uuidToURL(self):
        from plone.uuid.interfaces import IUUID
        from plone.app.uuid.utils import uuidToURL

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')
        portal.invokeFactory('Document', 'd2')

        d1 = portal['d1']
        uuid = IUUID(d1)

        self.assertEqual(d1.absolute_url(), uuidToURL(uuid))

    def test_uuidToObject(self):
        from Acquisition import aq_base
        from plone.uuid.interfaces import IUUID
        from plone.app.uuid.utils import uuidToObject

        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')
        portal.invokeFactory('Document', 'd2')

        d1 = portal['d1']
        uuid = IUUID(d1)

        self.assertEqual(aq_base(d1), aq_base(uuidToObject(uuid)))


class FunctionalTestCase(unittest.TestCase):

    layer = PLONE_APP_UUID_FUNCTIONAL_TESTING

    def test_uuid_view(self):

        from plone.uuid.interfaces import IUUID

        portal = self.layer['portal']
        app = self.layer['app']

        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')

        d1 = portal['d1']
        uuid = IUUID(d1)

        import transaction
        transaction.commit()

        from plone.testing.z2 import Browser
        browser = Browser(app)
        browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(TEST_USER_ID, TEST_USER_PASSWORD, )
        )

        browser.open('{0}/@@uuid'.format(d1.absolute_url()))
        self.assertEqual(uuid, browser.contents)

    def test_redirect_to_uuid_view(self):
        from plone.uuid.interfaces import IUUID

        portal = self.layer['portal']
        app = self.layer['app']

        setRoles(portal, TEST_USER_ID, ['Manager'])

        portal.invokeFactory('Document', 'd1')
        portal.invokeFactory('Document', 'd2')

        d1 = portal['d1']
        uuid = IUUID(d1)

        import transaction
        transaction.commit()

        from plone.testing.z2 import Browser
        browser = Browser(app)
        browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(TEST_USER_ID, TEST_USER_PASSWORD,)
        )

        url = '{0}/@@redirect-to-uuid/{1}'
        browser.open(url.format(portal.absolute_url(), uuid,))
        self.assertEqual(d1.absolute_url(), browser.url)

    def test_redirect_to_uuid_invalid_uuid(self):
        portal = self.layer['portal']
        app = self.layer['app']

        setRoles(portal, TEST_USER_ID, ['Manager'])

        import transaction
        transaction.commit()

        from plone.testing.z2 import Browser
        browser = Browser(app)
        browser.handleErrors = False
        browser.addHeader(
            'Authorization',
            'Basic {0}:{1}'.format(TEST_USER_ID, TEST_USER_PASSWORD, )
        )

        url = '{0}/@@redirect-to-uuid/gibberish'.format(portal.absolute_url())
        from zExceptions import NotFound
        with self.assertRaises(NotFound):
            browser.open(url)
