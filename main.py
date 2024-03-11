import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog

def datenbank_erstellen():
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()

    # Erstelle Tabelle für Gerichte
    c.execute('''CREATE TABLE IF NOT EXISTS gerichte
                 (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')

    # Erstelle Tabelle für Zutaten
    c.execute('''CREATE TABLE IF NOT EXISTS zutaten
                 (id INTEGER PRIMARY KEY, gericht_id INTEGER, name TEXT, menge TEXT,
                 FOREIGN KEY(gericht_id) REFERENCES gerichte(id))''')

    # Schließe die Verbindung
    conn.commit()
    conn.close()


def gericht_hinzufuegen(name):
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()
    c.execute("INSERT INTO gerichte (name) VALUES (?)", (name,))
    conn.commit()
    gericht_id = c.lastrowid
    conn.close()
    return gericht_id

def zutat_hinzufuegen(gericht_id, name, menge):
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()
    c.execute("INSERT INTO zutaten (gericht_id, name, menge) VALUES (?, ?, ?)",
              (gericht_id, name, menge))
    conn.commit()
    conn.close()

def gericht_loeschen(name):
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()

    # Zuerst die ID des Gerichts abrufen
    c.execute("SELECT id FROM gerichte WHERE name = ?", (name,))
    gericht_id = c.fetchone()
    if gericht_id:
        gericht_id = gericht_id[0]

        # Lösche alle Zutaten, die zum Gericht gehören
        c.execute("DELETE FROM zutaten WHERE gericht_id = ?", (gericht_id,))

        # Lösche dann das Gericht selbst
        c.execute("DELETE FROM gerichte WHERE id = ?", (gericht_id,))

        conn.commit()
    conn.close()

def rezept_anzeigen(name):
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()
    c.execute("SELECT id FROM gerichte WHERE name = ?", (name,))
    gericht_id = c.fetchone()[0]

    c.execute("SELECT name, menge FROM zutaten WHERE gericht_id = ?", (gericht_id,))
    zutaten = c.fetchall()

    print(f"Rezept für {name}:")
    for zutat in zutaten:
        print(f"- {zutat[0]}: {zutat[1]}")

    conn.close()

def hauptfenster():
    window = tk.Tk()
    window.title("Rezeptverwaltung")
    window.geometry("800x400")

    listbox_gerichte = tk.Listbox(window, selectmode=tk.EXTENDED)
    listbox_gerichte.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def details_anzeigen():
        auswahl_indices = listbox_gerichte.curselection()
        if not auswahl_indices:
            messagebox.showinfo("Info", "Bitte ein Gericht auswählen.")
            return
        ausgewaehltes_gericht = listbox_gerichte.get(auswahl_indices[0])  # Nehme das erste ausgewählte Gericht
        zutaten = zutaten_fuer_gericht_abrufen(ausgewaehltes_gericht)

        details_fenster = tk.Toplevel(window)
        details_fenster.title(f"Zutaten für {ausgewaehltes_gericht}")
        listbox_zutaten = tk.Listbox(details_fenster)
        listbox_zutaten.pack(fill=tk.BOTH, expand=True)

        for zutat, menge in zutaten:
            listbox_zutaten.insert(tk.END, f"{zutat}: {menge}")

    # Füge den "Details anzeigen"-Button zum Hauptfenster hinzu
    tk.Button(window, text="Details anzeigen", command=details_anzeigen).pack(padx=10, pady=5)

    def gerichte_loeschen():
        auswahl_indices = listbox_gerichte.curselection()
        ausgewaehlte_gerichte = [listbox_gerichte.get(i) for i in auswahl_indices]
        for gericht in ausgewaehlte_gerichte:
            gericht_loeschen(gericht)
        # Aktualisiere die Liste der Gerichte nach dem Löschen
        hauptfenster_aktualisieren(listbox_gerichte)

    def einkaufsliste_anzeigen():
        auswahl_indices = listbox_gerichte.curselection()
        ausgewaehlte_gerichte = [listbox_gerichte.get(i) for i in auswahl_indices]
        einkaufsliste = einkaufsliste_erstellen(ausgewaehlte_gerichte)
        # Zeige die Einkaufsliste in einem neuen Fenster oder einer Nachrichtenbox an
        einkaufsliste_text = "\n".join(f"{zutat}: {menge}" for zutat, menge in einkaufsliste.items())
        messagebox.showinfo("Einkaufsliste", einkaufsliste_text)

    # Füge den Button zum Hauptfenster hinzu
    tk.Button(window, text="Einkaufsliste erstellen", command=einkaufsliste_anzeigen).pack(padx=10, pady=5)
    tk.Button(window, text="Gerichte löschen", command=gerichte_loeschen).pack(padx=10, pady=5)

    tk.Button(window, text="Gericht und Zutaten hinzufügen",
              command=lambda: GerichtHinzufuegenFenster(tk.Toplevel(window))).pack(padx=10, pady=10)

    tk.Button(window, text="Gerichte aktualisieren",
              command=lambda: hauptfenster_aktualisieren(listbox_gerichte)).pack(padx=10, pady=5)

    hauptfenster_aktualisieren(listbox_gerichte)  # Aktualisiere die Liste beim Start

    window.mainloop()


def einkaufsliste_erstellen(ausgewaehlte_gerichte):
    alle_zutaten = {}
    for gericht in ausgewaehlte_gerichte:
        zutaten = zutaten_fuer_gericht_abrufen(gericht)
        for zutat, menge in zutaten:
            if zutat in alle_zutaten:
                alle_zutaten[zutat] = menge_addieren(alle_zutaten[zutat], menge)
            else:
                alle_zutaten[zutat] = menge
    return alle_zutaten

def zutaten_fuer_gericht_abrufen(gericht_name):
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()
    c.execute("SELECT id FROM gerichte WHERE name = ?", (gericht_name,))
    gericht_id = c.fetchone()[0]

    c.execute("SELECT name, menge FROM zutaten WHERE gericht_id = ?", (gericht_id,))
    zutaten = c.fetchall()
    conn.close()
    return zutaten


def menge_addieren(aktuelle_menge, hinzuzufuegende_menge):
    # Versuche, die Mengen in Zahlen zu konvertieren
    try:
        aktuelle_menge_zahl = float(aktuelle_menge)
        hinzuzufuegende_menge_zahl = float(hinzuzufuegende_menge)
        return str(aktuelle_menge_zahl + hinzuzufuegende_menge_zahl)
    except ValueError:
        # Falls die Konvertierung fehlschlägt, gib die ursprüngliche Menge zurück
        # oder implementiere eine spezifischere Logik zur Handhabung dieses Falls
        return aktuelle_menge


class GerichtHinzufuegenFenster:
    def __init__(self, master):
        self.master = master
        self.master.title("Gericht und Zutaten hinzufügen")
        self.master.geometry("500x600")

        self.zutaten_frame = tk.Frame(self.master)
        self.zutaten_frame.pack(padx=10, pady=10)

        tk.Label(self.master, text="Gerichtname:").pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.gericht_name_entry = tk.Entry(self.master)
        self.gericht_name_entry.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(self.master, text="Zutat hinzufügen", command=self.zutat_hinzufuegen_gui).pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Button(self.master, text="Gericht speichern", command=self.gericht_speichern).pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.zutaten_liste = []

    def zutat_hinzufuegen_gui(self):
        zutat_name = simpledialog.askstring("Zutat hinzufügen", "Zutatname:")
        menge = simpledialog.askstring("Menge hinzufügen", "Menge der Zutat:")
        if zutat_name and menge:
            self.zutaten_liste.append((zutat_name, menge))
            tk.Label(self.zutaten_frame, text=f"{zutat_name}: {menge}").pack()

    def gericht_speichern(self):
        gericht_name = self.gericht_name_entry.get()
        if gericht_name and self.zutaten_liste:
            gericht_id = gericht_hinzufuegen(gericht_name)  # Diese Funktion muss aus dem vorherigen Beispiel definiert sein
            for zutat_name, menge in self.zutaten_liste:
                zutat_hinzufuegen(gericht_id, zutat_name, menge)  # Diese Funktion muss aus dem vorherigen Beispiel definiert sein
            messagebox.showinfo("Erfolg", "Gericht mit Zutaten gespeichert")
            self.master.destroy()
        else:
            messagebox.showerror("Fehler", "Bitte geben Sie einen Gerichtnamen und mindestens eine Zutat ein")

def gerichte_abrufen():
    conn = sqlite3.connect('rezepte.db')
    c = conn.cursor()
    c.execute("SELECT name FROM gerichte")
    gerichte = c.fetchall()  # Das ergibt eine Liste von Tupeln
    conn.close()
    return [gericht[0] for gericht in gerichte]  # Konvertiere in eine Liste von Strings

def hauptfenster_aktualisieren(listbox):
    gerichte = gerichte_abrufen()
    listbox.delete(0, tk.END)  # Vorhandene Einträge löschen
    for gericht in gerichte:
        listbox.insert(tk.END, gericht)

class Zutat:
    def __init__(self, name, menge):
        self.name = name
        self.menge = menge

class Gericht:
    def __init__(self, name):
        self.name = name
        self.zutaten = []

    def zutat_hinzufuegen(self, zutat, menge):
        self.zutaten.append(Zutat(zutat, menge))

    def rezept_anzeigen(self):
        print(f"Rezept für {self.name}:")
        for zutat in self.zutaten:
            print(f"- {zutat.name}: {zutat.menge}")

if __name__ == "__main__":
    datenbank_erstellen()
    hauptfenster()
