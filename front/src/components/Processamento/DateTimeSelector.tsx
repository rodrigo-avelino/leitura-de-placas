// components/Processamento/DateTimeSelector.tsx (Compacto e Otimizado)

import { useState } from "react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { Calendar as CalendarIcon, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface DateTimeSelectorProps {
  dateTime: Date;
  onDateTimeChange: (date: Date) => void;
  disabled?: boolean;
}

const DateTimeSelector = ({ 
  dateTime, 
  onDateTimeChange, 
  disabled = false 
}: DateTimeSelectorProps) => {
  const [selectedDate, setSelectedDate] = useState<Date>(dateTime);
  const [time, setTime] = useState(format(dateTime, "HH:mm"));
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const handleDateSelect = (date: Date | undefined) => {
    if (date) {
      const [hours, minutes] = time.split(":");
      const newDate = new Date(date);
      newDate.setHours(parseInt(hours), parseInt(minutes));
      setSelectedDate(newDate);
      onDateTimeChange(newDate);
      setIsCalendarOpen(false);
    }
  };

  const handleTimeChange = (newTime: string) => {
    setTime(newTime);
    const [hours, minutes] = newTime.split(":");
    if (hours && minutes) {
      const newDate = new Date(selectedDate);
      newDate.setHours(parseInt(hours), parseInt(minutes));
      setSelectedDate(newDate);
      onDateTimeChange(newDate);
    }
  };

  const setNow = () => {
    const now = new Date();
    setSelectedDate(now);
    setTime(format(now, "HH:mm"));
    onDateTimeChange(now);
  };

  return (
    <div className={cn("space-y-4", disabled && "opacity-60 pointer-events-none")}>
      {/* Linha 1: Data e Horário */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Seletor de Data */}
        <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              disabled={disabled}
              className={cn(
                "w-full justify-start text-left font-normal h-11 border-2 transition-all",
                "hover:bg-muted/50 hover:border-muted-foreground/30",
                !selectedDate && "text-muted-foreground"
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4 text-primary shrink-0" />
              <div className="flex flex-col overflow-hidden">
                <span className="text-xs text-muted-foreground leading-tight">Data</span>
                <span className="font-semibold text-sm truncate">
                  {selectedDate 
                    ? format(selectedDate, "dd/MM/yyyy", { locale: ptBR }) 
                    : "Selecione"}
                </span>
              </div>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={handleDateSelect}
              initialFocus
              disabled={(date) => date > new Date()}
              className="rounded-lg border-2"
            />
          </PopoverContent>
        </Popover>

        {/* Seletor de Horário */}
        <div className="relative">
          <div 
            className={cn(
              "w-full h-11 border-2 rounded-md px-3 py-2 flex items-center gap-2 cursor-pointer transition-all hover:bg-muted/50 hover:border-muted-foreground/30",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            onClick={() => {
              if (!disabled) {
                const input = document.getElementById('time-input') as HTMLInputElement;
                input?.showPicker?.();
              }
            }}
          >
            <Clock className="h-4 w-4 text-primary shrink-0" />
            <div className="flex flex-col overflow-hidden flex-1">
              <span className="text-xs text-muted-foreground leading-tight">Horário</span>
              <span className="font-semibold text-sm truncate">
                {time || "00:00"}
              </span>
            </div>
            <Input
              id="time-input"
              type="time"
              value={time}
              onChange={(e) => handleTimeChange(e.target.value)}
              disabled={disabled}
              className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
            />
          </div>
        </div>
      </div>

      {/* Linha 2: Resumo + Botão Agora */}
      <div className="flex items-center justify-between gap-3 p-3 bg-muted/50 rounded-lg border border-border">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-muted-foreground mb-0.5">Registro</p>
          <p className="text-sm font-semibold text-foreground truncate">
            {format(selectedDate, "dd/MM/yyyy 'às' HH:mm", { locale: ptBR })}
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={setNow}
          disabled={disabled}
          className="shrink-0 h-9"
        >
          <Clock className="h-3.5 w-3.5 mr-1.5" />
          Agora
        </Button>
      </div>
    </div>
  );
};

export default DateTimeSelector;
