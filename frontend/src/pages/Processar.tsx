import { useState, useEffect } from "react";
import Navigation from "@/components/Layout/Navigation";
import UploadForm from "@/components/Processamento/UploadForm";
import ImageDisplay from "@/components/Processamento/ImageDisplay";
import AnaliseLog from "@/components/Processamento/AnaliseLog";
import DateTimeSelector from "@/components/Processamento/DateTimeSelector";

type StepStatus = "pending" | "processing" | "completed";

interface Step {
  id: number;
  name: string;
  description: string;
  status: StepStatus;
  imageUrl?: string;
}

const mockSteps: Step[] = [
  {
    id: 1,
    name: "Pré-processamento",
    description: "Conversão para cinza e suavização.",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?w=600&h=400&fit=crop",
  },
  {
    id: 2,
    name: "Bordas e Contorno",
    description: "Regiões candidatas destacadas.",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1581092918056-0c4c3acd3789?w=600&h=400&fit=crop",
  },
  {
    id: 3,
    name: "Detecção da Placa",
    description: "Placa localizada na imagem.",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?w=600&h=400&fit=crop",
  },
  {
    id: 4,
    name: "Recorte da Placa",
    description: "Crop da região estimada.",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600&h=400&fit=crop",
  },
  {
    id: 5,
    name: "Binarização",
    description: "Separação foreground/background para OCR",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=600&h=400&fit=crop",
  },
  {
    id: 6,
    name: "Caracteres Segmentados",
    description: "Candidatos identificados (ordem de leitura)",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1517420704952-d9f39e95b43e?w=600&h=400&fit=crop",
  },
  {
    id: 7,
    name: "OCR",
    description: "Leitura dos caracteres",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop",
  },
  {
    id: 8,
    name: "Validação e Armazenamento",
    description: "Padrão, consistência e registro.s",
    status: "pending",
    imageUrl: "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=400&fit=crop",
  },
];

const Processar = () => {
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [croppedPlate, setCroppedPlate] = useState<string | null>(null);
  const [steps, setSteps] = useState(mockSteps);
  const [currentStep, setCurrentStep] = useState(0);
  const [captureDateTime, setCaptureDateTime] = useState<Date>(new Date());

  useEffect(() => {
    if (uploadedImage && currentStep < steps.length) {
      const timer = setTimeout(() => {
        setSteps((prev) =>
          prev.map((step, index) => {
            if (index === currentStep) {
              return { ...step, status: "processing" };
            }
            if (index < currentStep) {
              return { ...step, status: "completed" };
            }
            return step;
          })
        );

        setTimeout(() => {
          setSteps((prev) =>
            prev.map((step, index) => {
              if (index === currentStep) {
                return { ...step, status: "completed" };
              }
              return step;
            })
          );
          
          // Simula o recorte da placa no passo 4
          if (currentStep === 3 && !croppedPlate) {
            setCroppedPlate(uploadedImage);
          }
          
          setCurrentStep((prev) => prev + 1);
        }, 1500);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [uploadedImage, currentStep, steps.length, croppedPlate]);

  const handleImageUpload = (imageUrl: string) => {
    setUploadedImage(imageUrl);
    setCroppedPlate(null);
    setSteps(mockSteps);
    setCurrentStep(0);
  };

  const handleClear = () => {
    setUploadedImage(null);
    setCroppedPlate(null);
    setSteps(mockSteps);
    setCurrentStep(0);
    setCaptureDateTime(new Date());
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <main className="container mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Processamento de Imagem
          </h1>
          <p className="text-muted-foreground">
            Faça upload de uma imagem de veículo para análise da placa
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <DateTimeSelector 
              dateTime={captureDateTime}
              onDateTimeChange={setCaptureDateTime}
            />
            
            {!uploadedImage ? (
              <UploadForm onImageUpload={handleImageUpload} />
            ) : (
              <ImageDisplay
                imageUrl={uploadedImage}
                croppedPlate={croppedPlate}
                onClear={handleClear}
              />
            )}
          </div>

          <div>
            <AnaliseLog steps={steps} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Processar;
