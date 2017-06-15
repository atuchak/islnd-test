# islnd-test

This Django app implements backend for partner balance service. Partner's balance is a sum of transactions. Transactions can increase or decrease account balance.

API provides changing of balance and keeps a history of its change.

Required models: Partner, Transaction

API requirements:
- created transaction could not be edited or deleted.
- input data should be validated
- all requests are trusted
- all transaction have the same currency
- there are hundreds of thousands of transactions per partner, balance calculation should take less than 1second


Transaction and AggregatedTransactions models are used as transaction storage.
Current partner balance is stored in Partner model and being updated when new transactions created. This approach permits to know the only current balance. For getting balance at any given time it needs to sum all of the transactions. It is not fast. For calculation speedup, we proposed to use table AggregatedTransactions. This table consists of daily balance aggregations. Thus balance at given date is the sum of daily aggregations + sum of transactions of the latest day.




Для хранения транзакций используется модели Transactions и AggregatedTransactions.
Текущий баланс хранится и апдейтится при появлении новых транзакций в модели партнера. 
Но такой подход позволяет знать баланс только текущий баланс, 
для получения баланса на другой участок времени необходими заново суммировать все транзакции, 
что может быть не быстро при большом количестве записей. 
Для ускороения предлагается использовать 2ю таблицу с агрегациями по дням. 
Таким образом, баланс на определеную дату вычисляется как сумма дневных агрегаций + 
все транзакции за последний день. Применя такой подход можно использовать более сложные агрегации, например еще и по месяцам (полная детализация на последний день, дневная за последний месяц )
(pros) должно работать быстрей
(cons) денормализация данных, запросы сложнее чем select sum(*) 


# Tests run

cd src ; pytest -v .