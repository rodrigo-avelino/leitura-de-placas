import { Link, useLocation } from "react-router-dom";
import { Camera, FileText, CarFront  } from "lucide-react";
import { cn } from "@/lib/utils";

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    {
      path: "/processar",
      label: "Processamento",
      icon: Camera,
      description: "Processar placas",
    },
    {
      path: "/registros",
      label: "Registros",
      icon: FileText,
      description: "Ver histórico",
    },
  ];

  return (
    <nav className="border-b border-border bg-gradient-to-r from-card via-card to-card/95 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-[1600px]">
        <div className="flex items-center justify-between h-20">
          {/* Logo/Brand */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 rounded-xl blur-lg animate-pulse" />
              <div className="relative flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-lg">
                <CarFront className="w-6 h-6 text-primary-foreground" />
              </div>
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                Leitura de Placas
              </h1>
              <p className="text-xs text-muted-foreground">
                Sistema de Reconhecimento
              </p>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center gap-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "group relative flex items-center gap-3 px-5 py-3 rounded-xl transition-all duration-300",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/25"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                  )}
                >
                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute inset-0 bg-gradient-to-r from-primary via-primary to-primary/80 rounded-xl blur-md opacity-50 animate-pulse" />
                  )}
                  
                  {/* Icon container */}
                  <div className={cn(
                    "relative flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-300",
                    isActive 
                      ? "bg-primary-foreground/10" 
                      : "bg-secondary/50 group-hover:bg-secondary"
                  )}>
                    <Icon className={cn(
                      "w-5 h-5 transition-transform duration-300",
                      isActive ? "scale-110" : "group-hover:scale-110"
                    )} />
                  </div>

                  {/* Text content */}
                  <div className="relative flex flex-col">
                    <span className={cn(
                      "font-semibold text-sm transition-colors",
                      isActive ? "text-primary-foreground" : ""
                    )}>
                      {item.label}
                    </span>
                    <span className={cn(
                      "text-xs transition-colors",
                      isActive 
                        ? "text-primary-foreground/70" 
                        : "text-muted-foreground/70 group-hover:text-muted-foreground"
                    )}>
                      {item.description}
                    </span>
                  </div>

                  {/* Hover indicator */}
                  {!isActive && (
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/0 via-primary/5 to-primary/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
