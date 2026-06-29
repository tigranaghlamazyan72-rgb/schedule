# Отображаем результаты расчетов прямо в веб-интерфейсе!
        st.markdown("<br><div class='section-label'>📊 Автоматический расчет таблицы:</div>", unsafe_allow_html=True)
        
        # Функция для динамического окрашивания строк в зависимости от часов
        def style_hours(row):
            minutes = row['Отработано_Минуты']
            hours = minutes / 60  # Переводим чистые минуты в часы для проверки условий
            
            if hours >= 8:
                bg_color = 'background-color: #d1fae5; color: #065f46;'  # Нежно-зеленый
            elif 6 <= hours < 8:
                bg_color = 'background-color: #fef3c7; color: #92400e;'  # Нежно-желтый
            else:
                bg_color = 'background-color: #fee2e2; color: #991b1b;'  # Нежно-красный
                
            return [bg_color] * len(row)

        # Применяем стилизацию к датафрейму
        styled_calc_df = calc_df_global.style.apply(style_hours, axis=1)
        
        st.dataframe(
            styled_calc_df, 
            column_config={
                "Имя": "Оператор", 
                "Первый_Матч": "Начало", 
                "Последний_Матч": "Конец (Матч)",
                "Количество": "Матчи", 
                "Отработано_Формат": "Часы:Мин", 
                "Отработано_Минуты": "Всего Минут"
            },
            use_container_width=True, 
            hide_index=True
        )
