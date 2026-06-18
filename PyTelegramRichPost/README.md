<h1>Телеграм теперь стал платформой для качественных лонгридов</h1>

<strong>Теперь щитпостить можно используя все прелести html и markdown</strong>

<img width="400" alt="изображение" src="https://github.com/user-attachments/assets/5b694af1-920f-49eb-8c32-c62689c7ede0" />

<hr/>

<h2>Но есть нюанс</h2>
<p>Постинг лонгридов доступен только с использованием BotAPI.</p>
<p>Самый простой и базовый пример постинга RichMessages (именно так это называется) через curl выглядит следующим образом:</p>

<pre>
  <code class="language-bash">
JSON_PAYLOAD="$(
  jq -nc \
    --arg chat_id "$CHAT_ID" \
    --arg text "$TEXT" \
    --arg is_rtl "$IS_RTL" '
      {
        chat_id: ((try ($chat_id | tonumber) catch $chat_id)),
        rich_message: {
          markdown: $text
        }
      }
      | if $is_rtl == "true" then
          .rich_message.is_rtl = true
        else
          .
        end
    '
)"
      </code>
</pre>

<pre>
  <code class="language-bash">
curl -sS -X POST \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" \
  "https://api.telegram.org/bot${BOT_TOKEN}/sendRichMessage" 
    
  </code>
</pre>

<blockquote><aside>Выглядит не очень и похоже на пердолинг? <cite>Ну, возможно</cite></aside></blockquote>


<hr/>
<hr/>

<h1>ПОЭТОМУ</h1>
<h2>ВАШЕМУ ВНИМАНИЮ ПРЕДСТАВЛЯЕТСЯ ПРИЛОЖЕНИЕ</h2>
<h3>ДЛЯ УДОБНОГО ПОСТИНГА ЛОНГРИДОВ</h3>

<img width="800" alt="Райан Гослинг в стиле киберпанка на фоне неонового ночного г" src="https://github.com/user-attachments/assets/b7baef88-2825-4853-af8b-0078cdd7d42d" />

<h3>В открытом доступе и доступно по адресу: <a href="http://lost.vakarian.website:9877/">lost.vakarian.website:9877</a></h3>

<p>Почему им стоит пользоваться?</p>
<ul>
  <li>Полностью открытый код</li>
  <li>Подробная инструкция</li>
  <li>Использование бота для постинга, который регистрирует сам пользователь</li>
  <li>Вся информация хранится <b>только на устройстве пользователя</b></li>
  <li>Сервер не сохраняет никакую пользовательскую информацию</li>
  <li>Возможность подтягивать html или markdown с GitHub</li>
  <li><b>ГОСЛИНГ НА ИКОНКЕ</b></li>
</ul>

<footer>А еще скоро я опубликую инструкцию по деплою на своем сервере.</footer>

