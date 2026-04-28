import React from 'react';
import BackHomeButtonIfLoggedOut from '@/components/BackHomeButtonIfLoggedOut';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'global CT Insights - Kontakt',
  description:
    'Kontaktieren Sie global CT für Fragen zu unseren KI-gestützten Dienstleistungen und Lösungen. Wir sind für Sie da unter +49 (0) 511 5151 07 10 oder info@globalct.com.',
  openGraph: {
    title: 'global CT Insights - Kontakt',
    description:
      'Kontaktieren Sie global CT für Fragen zu unseren KI-gestützten Dienstleistungen und Lösungen.',
    type: 'website',
  },
};

export default function ContactPage() {
  return (
    <div className="flex justify-center items-center min-h-screen">
      <div className="max-w-3xl mx-auto p-6">
        <h1 className="text-4xl font-bold mb-2">Kontakt</h1>
        <BackHomeButtonIfLoggedOut />

        <p className="mb-6 text-lg">
          Wenn Sie Fragen zu unseren Leistungen oder unserer Plattform haben,
          können Sie uns jederzeit über die untenstehenden Kontaktdaten
          erreichen.
        </p>

        <div className="space-y-4 text-base">
          <div>
            <h2 className="text-2xl font-semibold mb-1">Anschrift</h2>
            <p>
              Global CT
              <br />
              Services & Consulting GmbH
              <br />
              Lorbeerrosenweg 8<br />
              30916 Isernhagen
              <br />
              Deutschland
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold mb-1">Kontakt</h2>
            <p>
              Telefon:{' '}
              <a
                href="tel:+4951151510710"
                className="text-blue-600 hover:underline"
              >
                +49 (0) 511 5151 07 10
              </a>
            </p>
            <p>Fax: +49 (0) 511 5151 07 33</p>
            <p>
              E-Mail:{' '}
              <a
                href="mailto:info@globalct.com"
                className="text-blue-600 hover:underline"
              >
                info@globalct.com
              </a>
            </p>
          </div>
        </div>

        <p className="mt-8 text-sm text-gray-600">
          Bitte beachten Sie auch unsere{' '}
          <a href="/privacy" className="text-blue-600 hover:underline">
            Datenschutzerklärung
          </a>{' '}
          und{' '}
          <a href="/terms" className="text-blue-600 hover:underline">
            Nutzungsbedingungen
          </a>
          .
        </p>
      </div>
    </div>
  );
}
