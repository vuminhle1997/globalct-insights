import React from 'react';
import BackHomeButtonIfLoggedOut from '@/components/BackHomeButtonIfLoggedOut';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'global CT Insights - Nutzungsbedingungen',
  description:
    'Nutzungsbedingungen für die KI-gestützte Dokumentenanalyse-Plattform von global CT. Informationen zu Nutzungsvoraussetzungen, Pflichten, Datenschutz und rechtlichen Bestimmungen.',
  keywords:
    'Nutzungsbedingungen, AGB, Terms of Service, KI-Analyse, Dokumentenanalyse, LLama, RAG System',
  authors: [{ name: 'global CT' }],
  robots: 'index, follow',
  openGraph: {
    title: 'global CT Insights - Nutzungsbedingungen',
    description:
      'Nutzungsbedingungen für die KI-gestützte Dokumentenanalyse-Plattform von global CT.',
    type: 'website',
  },
};

export default function TermsOfService() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-4xl font-bold mb-2">Nutzungsbedingungen</h1>
      <BackHomeButtonIfLoggedOut />

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">1. Geltungsbereich</h2>
        <p>
          Die nachfolgenden Nutzungsbedingungen gelten für die Nutzung der von
          uns bereitgestellten Webanwendung, welche ein Retrieval-Augmented
          Generation (RAG) System auf Basis von LLama und Next.js beinhaltet.
          Mit der Nutzung der Plattform erkennen Sie diese Bedingungen als
          verbindlich an.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          2. Leistungsbeschreibung
        </h2>
        <p>
          Unsere Plattform erlaubt es Nutzer:innen, Dokumente hochzuladen und in
          einem interaktiven Chat auf Basis von LLama analysieren und auswerten
          zu lassen. Die bereitgestellten Informationen sind rein informativ und
          dürfen nicht als rechtliche, medizinische oder anderweitig
          professionelle Beratung verstanden werden.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          3. Nutzungsvoraussetzungen
        </h2>
        <p>
          Die Nutzung setzt voraus, dass Sie mindestens 18 Jahre alt sind oder
          mit Einwilligung Ihrer gesetzlichen Vertretung handeln. Ein
          Benutzerkonto kann für zusätzliche Funktionen erforderlich sein.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          4. Pflichten der Nutzer:innen
        </h2>
        <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
          <li>
            Keine rechtswidrigen, diskriminierenden oder beleidigenden Inhalte
            hochladen.
          </li>
          <li>
            Keine sensiblen personenbezogenen Daten Dritter ohne deren
            Einwilligung hochladen.
          </li>
          <li>
            Die Plattform nicht für automatisierte Abfragen oder
            Angriffsszenarien missbrauchen.
          </li>
          <li>
            Eigenverantwortlich handeln bei der Weiterverwendung von
            Ergebnissen.
          </li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          5. Inhalte & Verantwortung
        </h2>
        <p>
          Die generierten Antworten beruhen auf KI-Modellen und beinhalten keine
          Gewähr auf Richtigkeit oder Vollständigkeit. Wir übernehmen keine
          Haftung für Schäden, die durch fehlerhafte oder missverstandene
          Inhalte entstehen.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">6. Geistiges Eigentum</h2>
        <p>
          Die Plattform, der Quellcode und die Modelle (sofern nicht Open
          Source) unterliegen dem Urheberrecht. Nutzer:innen erhalten ein
          einfaches, nicht übertragbares Nutzungsrecht zur privaten Verwendung.
        </p>
        <p className="mt-2">
          Hochgeladene Inhalte verbleiben im Eigentum der Nutzer:innen. Die
          Plattform erhält lediglich ein temporäres Nutzungsrecht zur Analyse
          und Verarbeitung dieser Inhalte im Rahmen der angebotenen Dienste.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">
          7. Verfügbarkeit und Änderungen
        </h2>
        <p>
          Wir bemühen uns um eine möglichst unterbrechungsfreie Bereitstellung
          der Dienste, übernehmen jedoch keine Garantie für Verfügbarkeit,
          Fehlerfreiheit oder eine bestimmte Leistung. Funktionen können
          jederzeit angepasst, eingeschränkt oder entfernt werden.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">8. Haftung</h2>
        <p>
          Für Schäden, die aus der Nutzung oder Nichtverfügbarkeit der Dienste
          entstehen, haften wir nur bei vorsätzlichem oder grob fahrlässigem
          Verhalten. Eine weitergehende Haftung ist – soweit gesetzlich zulässig
          – ausgeschlossen.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">9. Datenschutz</h2>
        <p>
          Der Schutz Ihrer Daten ist uns wichtig. Bitte beachten Sie dazu unsere
          <a href="/privacy" className="text-blue-600 hover:underline ml-1">
            Datenschutzerklärung
          </a>
          .
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">10. Kündigung</h2>
        <p>
          Sie können die Nutzung der Plattform jederzeit beenden. Ein etwaig
          vorhandenes Konto kann von beiden Seiten jederzeit ohne Angabe von
          Gründen gekündigt werden.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">11. Schlussbestimmungen</h2>
        <p>
          Es gilt das Recht der Bundesrepublik Deutschland. Sollten einzelne
          Bestimmungen dieser Nutzungsbedingungen unwirksam sein oder werden,
          bleibt die Wirksamkeit der übrigen Regelungen unberührt.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-2">12. Kontakt</h2>
        <p>
          Bei Fragen zu diesen Nutzungsbedingungen erreichen Sie uns unter:
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
