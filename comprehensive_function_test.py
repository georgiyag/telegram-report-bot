#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест для проверки функций "в разработке" в коде бота.
"""

import os
import re
from datetime import datetime

class UnderDevelopmentChecker:
    """Проверяет код на наличие функций в разработке."""
    
    def __init__(self):
        self.src_dir = "src"
        self.under_dev_patterns = [
            r"Функция в разработке",
            r"в разработке",
            r"under development",
            r"заглушка",
            r"stub",
            r"TODO",
            r"FIXME"
        ]
        self.results = []
        
    def scan_file(self, filepath):
        """Сканирует файл на наличие функций в разработке."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
            found_issues = []
            for i, line in enumerate(lines, 1):
                for pattern in self.under_dev_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        found_issues.append({
                            'line': i,
                            'content': line.strip(),
                            'pattern': pattern
                        })
            
            return found_issues
            
        except Exception as e:
            print(f"Ошибка при чтении файла {filepath}: {e}")
            return []
    
    def scan_directory(self):
        """Сканирует всю директорию src."""
        print("🔍 Сканирование кода на наличие функций в разработке...")
        print("=" * 60)
        
        total_files = 0
        files_with_issues = 0
        total_issues = 0
        
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    total_files += 1
                    
                    issues = self.scan_file(filepath)
                    if issues:
                        files_with_issues += 1
                        total_issues += len(issues)
                        
                        print(f"\n📁 {filepath}:")
                        for issue in issues:
                            print(f"   Строка {issue['line']}: {issue['content']}")
                            print(f"   Паттерн: {issue['pattern']}")
                            print()
                        
                        self.results.append({
                            'file': filepath,
                            'issues': issues
                        })
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ")
        print("=" * 60)
        print(f"📁 Всего файлов проверено: {total_files}")
        print(f"⚠️  Файлов с проблемами: {files_with_issues}")
        print(f"🔍 Всего найдено проблем: {total_issues}")
        
        if total_issues == 0:
            print("\n🎉 Отлично! Функций в разработке не найдено!")
            print("   Бот готов к продакшену.")
        else:
            print(f"\n⚠️  ВНИМАНИЕ: Найдено {total_issues} функций в разработке!")
            print("   Необходимо завершить их реализацию.")
            
            print("\n📋 Список функций для реализации:")
            for result in self.results:
                print(f"\n📁 {result['file']}:")
                for issue in result['issues']:
                    print(f"   • Строка {issue['line']}: {issue['content'][:50]}...")
        
        # Сохранение отчета
        self.save_report(total_files, files_with_issues, total_issues)
        
        return total_issues == 0
    
    def save_report(self, total_files, files_with_issues, total_issues):
        """Сохраняет отчет в файл."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"under_development_report_{timestamp}.txt"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("ОТЧЕТ О ФУНКЦИЯХ В РАЗРАБОТКЕ\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего файлов: {total_files}\n")
            f.write(f"Файлов с проблемами: {files_with_issues}\n")
            f.write(f"Всего проблем: {total_issues}\n\n")
            
            if self.results:
                f.write("ДЕТАЛЬНЫЙ СПИСОК ПРОБЛЕМ:\n")
                f.write("-" * 30 + "\n")
                for result in self.results:
                    f.write(f"\nФайл: {result['file']}\n")
                    for issue in result['issues']:
                        f.write(f"  Строка {issue['line']}: {issue['content']}\n")
                        f.write(f"  Паттерн: {issue['pattern']}\n\n")
            else:
                f.write("Функций в разработке не найдено!\n")
        
        print(f"\n💾 Отчет сохранен: {report_filename}")

def main():
    """Главная функция."""
    checker = UnderDevelopmentChecker()
    
    if not os.path.exists(checker.src_dir):
        print(f"❌ Директория {checker.src_dir} не найдена!")
        return 1
    
    success = checker.scan_directory()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)