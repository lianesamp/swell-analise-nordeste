import { useState } from "react";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-blue-600 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          <div className="flex-shrink-0 font-bold text-xl cursor-pointer">
            Análise Swell Nordeste
          </div>

          {/* Menu desktop */}
          <div className="hidden md:flex space-x-8">
            <a
              href="#home"
              className="hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium"
            >
              Home
            </a>
            <a
              href="#resumo"
              className="hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium"
            >
              Resumo Anual
            </a>
            <a
              href="#resumo-mensal"
              className="hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium"
            >
              Resumo Mensal
            </a>
            <a
              href="#swell-ano"
              className="hover:text-gray-300 px-3 py-2 rounded-md text-sm font-medium"
            >
              Swell por Ano
            </a>
            
          </div>

          {/* Hamburger menu mobile */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md hover:bg-blue-500 focus:outline-none"
              aria-controls="mobile-menu"
              aria-expanded={isOpen}
            >
              <span className="sr-only">Abrir menu</span>
              {!isOpen ? (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              ) : (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Menu mobile */}
      {isOpen && (
        <div className="md:hidden bg-blue-700" id="mobile-menu">
          <a
            href="#home"
            className="block px-4 py-2 text-sm hover:bg-blue-600"
            onClick={() => setIsOpen(false)}
          >
            Home
          </a>
          <a
            href="#resumo"
            className="block px-4 py-2 text-sm hover:bg-blue-600"
            onClick={() => setIsOpen(false)}
          >
            Resumo Anual
          </a>
          <a
            href="#swell-ano"
            className="block px-4 py-2 text-sm hover:bg-blue-600"
            onClick={() => setIsOpen(false)}
          >
            Swell por Ano
          </a>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
