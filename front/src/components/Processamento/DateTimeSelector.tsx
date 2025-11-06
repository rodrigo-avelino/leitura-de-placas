import { useState, Dispatch, SetStateAction } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale"; // IMPORTAÇÃO CORRIGIDA

interface DateTimeSelectorProps {
  dateTime: Date;
  onDateTimeChange: Dispatch<SetStateAction<Date>>;
  disabled: boolean; // Propriedade obrigatória
}

const DateTimeSelector = ({
  dateTime,
  onDateTimeChange,
  disabled,
}: DateTimeSelectorProps) => {
  // Converte o objeto Date para strings de input (YYYY-MM-DD e HH:MM)
  // O uso de 'ptBR' na formatação final é cosmético, mas não afeta os inputs date/time
  const dateString = format(dateTime, "yyyy-MM-dd");
  const timeString = format(dateTime, "HH:mm");

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDateString = e.target.value;
    // Combina a nova data com a hora existente
    const combinedDateTime = parseISO(`${newDateString}T${timeString}`);
    onDateTimeChange(combinedDateTime);
  };

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTimeString = e.target.value;
    // Combina a data existente com a nova hora
    // Usamos a string 'dateString' existente para manter a data
    const combinedDateTime = parseISO(`${dateString}T${newTimeString}`);
    onDateTimeChange(combinedDateTime);
  };

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        <h3 className="text-lg font-semibold text-foreground">
          Data e Hora da Captura
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">
              Data
            </label>
            <Input
              type="date"
              value={dateString}
              onChange={handleDateChange}
              disabled={disabled} // Aplica o disabled
              className="h-10"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground mb-1 block">
              Horário
            </label>
            <Input
              type="time"
              value={timeString}
              onChange={handleTimeChange}
              disabled={disabled} // Aplica o disabled
              className="h-10"
            />
          </div>
        </div>
        <p className="text-sm text-muted-foreground pt-2">
          Data/Hora selecionada:{" "}
          <span className="font-medium text-foreground">
            {format(dateTime, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
          </span>
        </p>
      </CardContent>
    </Card>
  );
};

export default DateTimeSelector;
