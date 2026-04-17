import { AssemblyStep, Part } from '@/app/types';
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  PDFDownloadLink,
} from '@react-pdf/renderer';

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontSize: 11,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 30,
    borderBottomWidth: 2,
    borderBottomColor: '#000',
    paddingBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 12,
    color: '#666',
  },
  section: {
    marginVertical: 15,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 10,
    backgroundColor: '#f0f0f0',
    padding: 5,
  },
  stepContainer: {
    marginVertical: 10,
    padding: 10,
    border: '1pt solid #ddd',
    borderRadius: 4,
  },
  stepNumber: {
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  stepTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  stepDescription: {
    fontSize: 10,
    marginBottom: 5,
    lineHeight: 1.4,
  },
  partsGrid: {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  partBadge: {
    fontSize: 9,
    padding: 3,
    backgroundColor: '#e3f2fd',
    borderRadius: 2,
    marginRight: 5,
    marginBottom: 5,
  },
  footer: {
    marginTop: 20,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    fontSize: 9,
    color: '#999',
    textAlign: 'center',
  },
});

interface AssemblyInstructionsPDFProps {
  fileName: string;
  parts: Part[];
  steps: AssemblyStep[];
}

export function AssemblyInstructionsPDF({
  fileName,
  parts,
  steps,
}: AssemblyInstructionsPDFProps) {
  return (
    <Document>
      {/* Cover Page */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Instrukcja Montażu</Text>
          <Text style={styles.subtitle}>WEBLE - Instrukcje montażu mebli</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Informacje o projekcie</Text>
          <View style={{ marginBottom: 10 }}>
            <Text>Plik: {fileName}</Text>
            <Text>Liczba części: {parts.length}</Text>
            <Text>Liczba kroków: {steps.length}</Text>
            <Text>Data wygenerowania: {new Date().toLocaleDateString('pl-PL')}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Spis treści</Text>
          <View>
            <Text>1. Części komponenty</Text>
            <Text>2. Instrukcje montażu</Text>
          </View>
        </View>

        <View style={styles.footer}>
          <Text>© 2024 WEBLE. Wszystkie prawa zastrzeżone.</Text>
        </View>
      </Page>

      {/* Parts Page */}
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Części komponenty</Text>
        </View>

        <View style={styles.section}>
          {parts.map((part, idx) => (
            <View key={idx} style={styles.stepContainer}>
              <Text style={styles.stepTitle}>
                Część {part.id} {part.quantity > 1 ? `(×${part.quantity})` : ''}
              </Text>
              <Text style={styles.stepDescription}>
                Typ: {part.part_type}
              </Text>
              <Text style={styles.stepDescription}>
                Objętość: {part.volume.toFixed(2)} cm³
              </Text>
              <Text style={styles.stepDescription}>
                Wymiary:{' '}
                {Object.entries(part.dimensions)
                  .map(([k, v]) => `${k}: ${v.toFixed(1)}`)
                  .join(', ')}
              </Text>
            </View>
          ))}
        </View>

        <View style={styles.footer}>
          <Text>Strona 2 - Części komponenty</Text>
        </View>
      </Page>

      {/* Assembly Steps Pages */}
      {steps.map((step, stepIdx) => (
        <Page key={stepIdx} size="A4" style={styles.page}>
          <View style={styles.header}>
            <Text style={styles.title}>
              Krok {step.step_number} z {steps.length}
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.stepTitle}>{step.title}</Text>
            <Text style={styles.stepDescription}>{step.description}</Text>

            {step.detail_description && (
              <Text style={[styles.stepDescription, { marginTop: 10, fontStyle: 'italic' }]}>
                {step.detail_description}
              </Text>
            )}
          </View>

          {/* Parts Involved */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Części zaangażowane</Text>
            <View style={styles.partsGrid}>
              {step.part_indices.map((partIdx) => (
                <View key={partIdx} style={styles.partBadge}>
                  <Text>Część {partIdx}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Assembly Sequence */}
          {step.assembly_sequence && step.assembly_sequence.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Sekwencja montażu</Text>
              {step.assembly_sequence.map((seq, idx) => (
                <Text key={idx} style={styles.stepDescription}>
                  {idx + 1}. {seq}
                </Text>
              ))}
            </View>
          )}

          {/* Tips */}
          {step.tips && step.tips.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Wskazówki</Text>
              {step.tips.map((tip, idx) => (
                <Text key={idx} style={styles.stepDescription}>
                  • {tip}
                </Text>
              ))}
            </View>
          )}

          {/* Warnings */}
          {step.warnings && step.warnings.length > 0 && (
            <View
              style={[
                styles.section,
                { borderLeftWidth: 3, borderLeftColor: '#d32f2f', paddingLeft: 10 },
              ]}
            >
              <Text style={[styles.sectionTitle, { backgroundColor: '#ffebee' }]}>
                Ostrzeżenia
              </Text>
              {step.warnings.map((warn, idx) => (
                <Text key={idx} style={styles.stepDescription}>
                  ⚠ {warn}
                </Text>
              ))}
            </View>
          )}

          <View style={styles.footer}>
            <Text>Strona {stepIdx + 3} - Krok montażu</Text>
          </View>
        </Page>
      ))}
    </Document>
  );
}

export function AssemblyInstructionsPDFDownload({
  fileName,
  parts,
  steps,
}: AssemblyInstructionsPDFProps) {
  return (
    <PDFDownloadLink
      document={
        <AssemblyInstructionsPDF fileName={fileName} parts={parts} steps={steps} />
      }
      fileName={`instrukcja-montazu-${Date.now()}.pdf`}
      style={{
        padding: '8px 16px',
        backgroundColor: '#059669',
        color: 'white',
        textDecoration: 'none',
        borderRadius: '4px',
        fontWeight: 'bold',
        display: 'inline-block',
      }}
    >
      {({ blob, url, loading, error }) =>
        loading ? 'Generowanie PDF...' : 'Pobierz instrukcję (PDF)'
      }
    </PDFDownloadLink>
  );
}
