
file=$*
#beancount_main=my.beancount
beancount_main=ledger.beancount

bean-identify my.import "$file"
bean-extract my.import -f $beancount_main "$file"
