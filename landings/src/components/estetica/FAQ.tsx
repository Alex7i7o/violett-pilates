import React from 'react';

export function FAQ() {
  const faqs = [
    {
      q: "¿Cuándo debo iniciar las sesiones de postquirúrgico?",
      a: "Depende del tipo de intervención y la autorización expresa de su médico cirujano. En procedimientos como lipoescultura o dermolipectomía, usualmente se aconseja comenzar entre el 3.° y el 7.° día posterior a la cirugía para facilitar la reabsorción del líquido linfático antes de que se organice en fibrosis."
    },
    {
      q: "¿El drenaje linfático postoperatorio tiene que doler?",
      a: "No. El drenaje linfático manual auténtico es suave, rítmico y superficial. Nunca debe causar dolor punzante, rotura vascular ni generar hematomas. Nuestra técnica respeta la hipersensibilidad de la zona intervenida."
    },
    {
      q: "¿Se requiere orden médica para comenzar?",
      a: "Para tratamientos postquirúrgicos solicitamos el apto o derivación de su cirujano de cabecera junto con los datos de contacto del profesional para trabajar de forma alineada ante cualquier observación."
    },
    {
      q: "¿Qué medios de pago aceptan?",
      a: "Aceptamos transferencias bancarias, efectivo, tarjetas de débito y crédito. Contamos con planes de pago bonificados en módulos de 5 y 10 sesiones."
    }
  ];

  return (
    <section className="py-24 bg-primary-light/30">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <h2 className="text-3xl font-extrabold text-primary-main mb-12 text-center tracking-tight">Preguntas Frecuentes</h2>
        <div className="space-y-6">
          {faqs.map((faq, idx) => (
            <div key={idx} className="bg-white rounded-2xl p-6 border border-primary-light shadow-sm">
              <h4 className="text-lg font-bold text-foreground mb-3">{faq.q}</h4>
              <p className="text-muted leading-relaxed">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
