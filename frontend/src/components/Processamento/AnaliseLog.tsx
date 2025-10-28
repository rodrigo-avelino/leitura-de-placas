import { Card } from "@/components/ui/card";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface AnaliseStep {
  id: number;
  name: string;
  description: string;
  status: "completed" | "processing" | "pending";
  imageUrl?: string;
}

interface AnaliseLogProps {
  steps: AnaliseStep[];
}

const AnaliseLog = ({ steps }: AnaliseLogProps) => {
  return (
    <Card className="p-6 h-full">
      <h3 className="text-lg font-semibold text-foreground mb-6">Log de Análise</h3>
      
      <Accordion type="single" collapsible className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className={cn(
                "rounded-full p-1 mt-3",
                step.status === "completed" && "bg-success/10",
                step.status === "processing" && "bg-accent/10",
                step.status === "pending" && "bg-muted"
              )}>
                {step.status === "completed" && (
                  <CheckCircle2 className="w-5 h-5 text-success" />
                )}
                {step.status === "processing" && (
                  <Loader2 className="w-5 h-5 text-accent animate-spin" />
                )}
                {step.status === "pending" && (
                  <Circle className="w-5 h-5 text-muted-foreground" />
                )}
              </div>
              
              {index < steps.length - 1 && (
                <div className={cn(
                  "w-0.5 flex-1 mt-2",
                  step.status === "completed" ? "bg-success/30" : "bg-border"
                )} />
              )}
            </div>
            
            <AccordionItem 
              value={`step-${step.id}`} 
              className="flex-1 border-0"
            >
              <AccordionTrigger className={cn(
                "hover:no-underline py-3",
                step.status === "pending" && "opacity-50 cursor-not-allowed",
                step.status === "pending" && "pointer-events-none"
              )}>
                <div className="flex-1 text-left">
                  <h4 className={cn(
                    "font-semibold mb-1",
                    step.status === "pending" && "text-muted-foreground",
                    step.status !== "pending" && "text-foreground"
                  )}>
                    {step.name}
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </AccordionTrigger>
              
              {step.status !== "pending" && (
                <AccordionContent className="pb-4">
                  <div className="mt-2 rounded-lg overflow-hidden border border-border bg-muted/20">
                    {step.imageUrl ? (
                      <img 
                        src={step.imageUrl} 
                        alt={`Resultado da etapa: ${step.name}`}
                        className="w-full h-auto"
                      />
                    ) : (
                      <div className="aspect-video flex items-center justify-center text-muted-foreground">
                        <p className="text-sm">Imagem de exemplo para {step.name}</p>
                      </div>
                    )}
                  </div>
                </AccordionContent>
              )}
            </AccordionItem>
          </div>
        ))}
      </Accordion>
    </Card>
  );
};

export default AnaliseLog;
