import React from 'react';
import BackHomeButtonIfLoggedOut from '@/components/BackHomeButtonIfLoggedOut';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'global CT Insights | Datenschutzerklärung',
  description:
    'Datenschutzerklärung für global CT Insights - Informationen über die Erhebung, Verarbeitung und Speicherung Ihrer personenbezogenen Daten bei der Nutzung unseres RAG-Systems.',
  keywords:
    'Datenschutz, Privacy Policy, DSGVO, global CT, Insights, Datensicherheit',
  openGraph: {
    title: 'global CT Insights | Datenschutzerklärung',
    description:
      'Datenschutzerklärung für global CT Insights - Informationen über Datenschutz und DSGVO-Konformität.',
  },
};

export default function PrivacyPolicy() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-4xl font-bold mb-2">Datenschutzerklärung</h1>
      <BackHomeButtonIfLoggedOut />

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">1. Einleitung</h2>
        <p>
          Wir freuen uns über Ihr Interesse an unserer Webanwendung. Der Schutz
          Ihrer personenbezogenen Daten ist uns ein wichtiges Anliegen. In
          dieser Datenschutzerklärung informieren wir Sie über die Art, den
          Umfang und den Zweck der Verarbeitung personenbezogener Daten im
          Rahmen der Nutzung unseres RAG-Systems basierend auf LLama und
          Next.js.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">2. Verantwortlicher</h2>
        <p>
          Verantwortlich für die Datenverarbeitung im Sinne der
          Datenschutz-Grundverordnung (DSGVO) ist:
        </p>
        <div className="mt-2 ml-4">
          <p>Global CT Services & Consulting GmbH</p>
          <p>E-Mail: info@globalct.com</p>
          <p>Telefon: +49 (0) 511 5151 07 10</p>
          <p>Fax: +49 (0) 511 5151 07 33</p>
          <p>Sitz: Lorbeerrosenweg 8, 30916 Isernhagen</p>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          3. Erhebung und Speicherung personenbezogener Daten
        </h2>
        <p>Wir erheben und speichern personenbezogene Daten, wenn Sie:</p>
        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
          <li>uns eine Datei zur Analyse hochladen,</li>
          <li>eine Chat-Konversation mit dem RAG-System starten,</li>
          <li>
            uns kontaktieren oder ein Benutzerkonto erstellen (sofern
            vorhanden).
          </li>
        </ul>
        <p className="mt-2">
          Zu den verarbeiteten Daten gehören unter anderem: Name, E-Mail-Adresse
          (falls angegeben), Chatverlauf, hochgeladene Inhalte und technische
          Metadaten (z. B. IP-Adresse, Browsertyp, Zeitstempel).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          4. Zweck der Datenverarbeitung
        </h2>
        <p>Die Verarbeitung Ihrer Daten erfolgt zu folgenden Zwecken:</p>
        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
          <li>
            Zur Bereitstellung der RAG-Funktionalitäten (Frage-Antwort-Systeme)
          </li>
          <li>Zur Verbesserung unseres Angebots und der Nutzererfahrung</li>
          <li>Zur Fehleranalyse und Sicherheit</li>
          <li>Zur Kontaktaufnahme, wenn Sie uns kontaktieren</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">5. Weitergabe von Daten</h2>
        <p>
          Eine Weitergabe Ihrer Daten an Dritte erfolgt grundsätzlich nicht, es
          sei denn:
        </p>
        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
          <li>Sie haben ausdrücklich eingewilligt,</li>
          <li>es ist zur Erfüllung eines Vertrages erforderlich,</li>
          <li>es besteht eine gesetzliche Verpflichtung dazu.</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          6. Speicherung und Löschung
        </h2>
        <p>
          Personenbezogene Daten werden nur so lange gespeichert, wie es für die
          Erreichung der genannten Zwecke erforderlich ist. Sie haben jederzeit
          das Recht auf Löschung Ihrer Daten, sofern keine gesetzlichen
          Aufbewahrungsfristen entgegenstehen.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">7. Ihre Rechte</h2>
        <p>Sie haben das Recht:</p>
        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
          <li>Auskunft über Ihre gespeicherten Daten zu erhalten,</li>
          <li>unrichtige Daten berichtigen zu lassen,</li>
          <li>die Löschung Ihrer Daten zu verlangen,</li>
          <li>der Verarbeitung zu widersprechen,</li>
          <li>eine Beschwerde bei der Aufsichtsbehörde einzureichen.</li>
        </ul>
        <p className="mt-2">
          Bitte kontaktieren Sie uns unter den oben genannten Kontaktdaten.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          8. Einsatz von Analyse-Tools
        </h2>
        <p>
          Wir verwenden keine externen Tracking- oder Analyse-Tools wie Google
          Analytics. Server-Logs werden ausschließlich zur Fehlerbehebung und
          Sicherheitsanalyse genutzt.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">9. Cookies</h2>
        <p>
          Wir verwenden technische Cookies, um Ihre Sitzung (Session-Cookie) und
          Ihre Authentifizierung (falls vorhanden) zu verwalten. Diese Cookies
          enthalten keine personenbezogenen Daten und werden nach Sitzungsende
          automatisch gelöscht.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">10. Datensicherheit</h2>
        <p>
          Wir setzen technische und organisatorische Maßnahmen ein, um Ihre
          Daten gegen Verlust, Zerstörung oder unbefugten Zugriff zu schützen.
          Dazu gehören Verschlüsselung, Zugriffskontrollen und regelmäßige
          Sicherheitsupdates.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">11. Änderungen</h2>
        <p>
          Wir behalten uns vor, diese Datenschutzerklärung bei Änderungen
          unseres Angebots oder bei rechtlichen Änderungen anzupassen. Bitte
          informieren Sie sich regelmäßig auf dieser Seite.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-2">12. Kontakt</h2>
        <p>
          Bei Fragen zur Verarbeitung Ihrer personenbezogenen Daten oder zur
          Ausübung Ihrer Rechte kontaktieren Sie uns bitte per E-Mail:
          <a
            href="mailto:info@globalct.com"
            className="text-blue-600 hover:underline ml-1"
          >
            info@globalct.com
          </a>
        </p>
      </section>
    </div>
  );
}
